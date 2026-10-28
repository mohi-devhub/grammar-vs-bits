"""Derive all pilot summaries and projections from saved events and rates."""
import argparse
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from qunti.common import ROOT, now, read_jsonl, write_json
from qunti.scoring import score
from qunti.diagnostics import taxonomy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", required=True)
    args = parser.parse_args()
    root = ROOT / "results/pilot" / args.batch_id
    events = read_jsonl(root / "events.jsonl")
    rows = [x for x in events if x["kind"] == "generation"]
    protocol = json.loads((ROOT / "configs/protocol.json").read_text())["pilot"]
    pilot_ids = json.loads((ROOT / "data/pilot_ids.json").read_text())
    expected = {(q, arm, item) for q in protocol["precisions"] for arm in protocol["arms"] for item in pilot_ids}
    observed = {(r["quant"], r["condition"], r["id"]) for r in rows}
    coverage_ok = observed == expected and len(rows) == len(expected)
    items = {x["id"]: x for x in read_jsonl(ROOT / "data/frozen.jsonl")}
    scored, groups = [], defaultdict(list)
    for row in rows:
        result = score(items[row["id"]], row["text"], completed=row["completed"])
        result["taxonomy"] = taxonomy(items[row["id"]], row["text"], result)
        scored.append({**row, "score": result})
        groups[(row["quant"], row["condition"])].append(scored[-1])
    (root / "scored.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in scored))
    rates_path = ROOT / f"results/ops/{args.batch_id}_rates.json"
    rates = json.loads((rates_path if rates_path.exists() else ROOT / "results/ops/rates.json").read_text())
    starts = [e for e in events if e["kind"] == "session_started"]
    if len(starts) > 1:
        raise RuntimeError("Multiple worker sessions: do not combine them into one matched pilot")
    gpu_type = starts[0]["metadata"].get("gpu_type", "L4") if starts else None
    if rows and any(r.get("gpu_type", gpu_type) != gpu_type for r in rows):
        raise RuntimeError("Mixed GPU types within pilot; report separately, never pool")
    gpu_rate_key = "gpu_hour_cost_a10g" if gpu_type == "A10" else "gpu_hour_cost_l4"
    gpu_hour = Decimal(rates[gpu_rate_key]) + 2 * Decimal(rates["cpu_hour_cost"]) + 16 * Decimal(rates["mem_gib_hour_cost"])
    cpu_hour = 2 * Decimal(rates["cpu_hour_cost"]) + 16 * Decimal(rates["mem_gib_hour_cost"])
    finished = next((e for e in events if e["kind"] == "session_finished"), None)
    supervisor_finished = next((e for e in events if e["kind"] == "supervisor_finished"), None)
    worker_seconds = finished["active_function_seconds"] if finished else None
    prep_path = ROOT / f"results/ops/{args.batch_id}_model_artifacts.json"
    prep = json.loads((prep_path if prep_path.exists() else ROOT / "results/ops/model_artifacts.json").read_text())
    cells = []
    inference_seconds = 0.0
    quant_wall = {}
    for event in events:
        if event["kind"] == "precision_finished":
            inference_seconds += event["batch_wall_seconds"]
            quant_wall[event["precision"]] = event["batch_wall_seconds"]
    for (quant, arm), cell in sorted(groups.items()):
        cells.append({"quant": quant, "condition": arm, "attempts": len(cell),
                      "correct": sum(x["score"]["correct"] for x in cell),
                      "format_failures": sum(x["score"]["invalid_json_or_format"] for x in cell),
                      "status_counts": dict(Counter(x["status"] for x in cell)),
                      "mean_request_seconds": sum(x["elapsed_seconds"] for x in cell) / len(cell)})
    summary = {"created_at": now(), "batch": args.batch_id, "attempted_generations": len(rows),
               "gpu_type": gpu_type, "gpu_metadata": starts[0]["metadata"] if starts else None,
               "planned_generations": 300, "complete": coverage_ok and finished is not None,
               "coverage_matches_frozen_pilot": coverage_ok,
               "responses_received": sum("response" in row for row in rows),
               "finished_responses": sum(row["completed"] for row in rows),
               "status_counts": dict(Counter(row["status"] for row in rows)),
               "cells": cells, "measured_inference_batch_wall_seconds": inference_seconds,
               "measured_gpu_function_seconds": worker_seconds,
               "measured_supervisor_body_seconds": supervisor_finished["active_function_seconds"] if supervisor_finished else None,
               "measured_cpu_preparation_function_seconds": prep["active_function_seconds"],
               "resource_rate_gpu_container_usd_hour": float(gpu_hour),
               "resource_rate_cpu_container_usd_hour": float(cpu_hour),
               "cost_scope": "Timing-based resource estimates exclude platform startup, image builds, idle, post-timer cleanup/volume commits and storage; tagged metering is separate.",
               "timer_definitions": {"cpu_preparation": "Function entry through manifest construction, before source-weight cleanup and volume commit",
                                     "gpu_worker": "Worker-body entry through completed precisions and server shutdown, before final volume commit"}}
    if rows and worker_seconds is not None:
        inference = inference_seconds * float(gpu_hour) / 3600
        function_cost = worker_seconds * float(gpu_hour) / 3600 + prep["active_function_seconds"] * float(cpu_hour) / 3600
        summary.update({"timed_inference_resource_cost_usd": inference,
                        "timed_preparation_and_gpu_resource_cost_usd": function_cost,
                        "timed_inference_usd_per_attempt": inference / len(rows),
                        "timed_preparation_and_gpu_usd_per_attempt": function_cost / len(rows),
                        "timed_preparation_and_gpu_usd_per_unique_item": function_cost / 50})
        if supervisor_finished:
            supervisor_rate = float(Decimal('0.25') * Decimal(rates['cpu_hour_cost']) + Decimal(rates['mem_gib_hour_cost']))
            supervisor_cost = supervisor_finished['active_function_seconds'] * supervisor_rate / 3600
            summary['supervisor_cpu_resource_ceiling_estimate_usd'] = supervisor_cost
            summary['gpu_prep_supervisor_body_resource_estimate_usd'] = function_cost + supervisor_cost
            summary['gpu_prep_supervisor_body_usd_per_generation'] = (function_cost + supervisor_cost) / summary['responses_received'] if summary['responses_received'] else None
        received = summary["responses_received"]
        summary["timed_inference_usd_per_generation"] = inference / received if received else None
        summary["timed_preparation_and_gpu_usd_per_generation"] = function_cost / received if received else None
        summary["calibration_usable"] = (coverage_ok and len(rows) == received == 300 and finished is not None
                                             and {r["status"] for r in rows} <= {"ok", "token_limit"})
        if not summary["calibration_usable"]:
            summary["projection_unavailable_reason"] = "Incomplete or operationally failed pilot cannot calibrate the unchanged full run"
        if summary["calibration_usable"]:
            # Main matrix omits pilot-only Q8. Pilot arms were interleaved, so use
            # their pooled observed batch throughput; never call this per-arm GPU billing.
            qwen_seconds = sum(quant_wall[q] * 40 for q in ("F16", "Q4_K_M"))
            projection = {"qwen_main_8000_calls_seconds_at_observed_two_arm_throughput": qwen_seconds,
                          "hardware_assumption": "Same GPU type as this pilot; no cross-GPU speed equivalence assumed",
                          "qwen_main_8000_calls_resource_usd_at_observed_throughput": qwen_seconds * float(gpu_hour) / 3600,
                          "unmeasured": ["Llama model throughput", "loose and trigger-strict generation lengths", "five-run scheduling variation", "additional image/preparation/startup/storage costs"],
                          "not_a_full_run_authorization": True}
            projection["preliminary_not_a_guaranteed_cost_bound"] = True
            projection["pilot_all_requests_returned_responses"] = received == 300
            # These factors are explicitly sensitivity assumptions, not observations.
            projection["whole_study_scenarios"] = [{"assumed_llama_cost_multiple_of_qwen_per_model": m,
                "assumed_loose_trigger_pool_multiplier": a,
                "inference_resource_usd": qwen_seconds * (1 + 2 * m) * a * float(gpu_hour) / 3600}
                for m in (1, 3, 5) for a in (1, 2)]
            summary["projection"] = projection
    write_json(root / "summary.json", summary)
    lines = ["# Qwen pilot report", "", f"Generated from `{root.relative_to(ROOT)}/events.jsonl` at {summary['created_at']}.", "",
             f"{len(rows)} / 300 planned attempts; {summary['responses_received']} returned responses; "
             f"{summary['finished_responses']} completed responses. No failed attempt is removed.", "",
             "| Precision | Decoder | Attempts | BFCL correct | Format failures | Status counts |",
             "| --- | --- | ---: | ---: | ---: | --- |"]
    lines[4:4] = [f"Allocated GPU type: {gpu_type or 'not allocated'}. All pilot arms and precisions use the same worker.", ""]
    if not summary["complete"]:
        lines[4:4] = ["**Incomplete pilot. Unstarted requests have no score or measured generation time. "
                      "A full-run cost forecast cannot be validated from this incomplete session.**", ""]
    for cell in cells:
        lines.append(f"| {cell['quant']} | {cell['condition']} | {cell['attempts']} | {cell['correct']} | {cell['format_failures']} | {cell['status_counts']} |")
    lines += ["", "This pilot calibrates runtime and implementation; it does not establish the four-arm, five-run research result.", ""]
    if rows and worker_seconds is not None:
        lines += [f"Measured inference batch wall time: {inference_seconds:.3f} seconds. "
                  f"GPU function time (including loading/warmup): {worker_seconds:.3f} seconds. "
                  f"CPU preparation function time: {prep['active_function_seconds']:.3f} seconds.", "",
                  f"Timing-based inference resource estimate: ${inference:.6f} total; "
                  f"${inference / len(rows):.8f} per attempted request. "
                  f"Preparation plus GPU function resource estimate: ${function_cost:.6f}; "
                  f"${function_cost / len(rows):.8f} per attempt; ${function_cost / 50:.6f} per unique item.", "",
                  "These timing estimates exclude platform startup, image builds, idle, post-timer cleanup/volume commits, and persistent storage. "
                  "Use the separate saved tagged billing report for metered costs; account-wide changes include other projects.", ""]
    if "projection" in summary:
        lines += [f"Qwen's 8,000 full-design calls extrapolate to ${projection['qwen_main_8000_calls_resource_usd_at_observed_throughput']:.4f} "
                  "of inference resources **if** both new decoder arms match the pooled free/whole-strict throughput. "
                  "Llama speed and lazy/permissive-arm output lengths have not been measured.", "",
                  "| Assumed per-Llama cost relative to Qwen | Assumed whole-grid throughput cost multiplier | Full-grid inference USD |",
                  "| ---: | ---: | ---: |"]
        for scenario in projection['whole_study_scenarios']:
            lines.append(f"| {scenario['assumed_llama_cost_multiple_of_qwen_per_model']} | {scenario['assumed_loose_trigger_pool_multiplier']} | {scenario['inference_resource_usd']:.4f} |")
        lines += ["", "Scenario factors are assumptions, not measurements, and exclude further setup/storage costs. "
                  "This table is not a guaranteed bound or full-run authorization. Preserve all models, arms, and runs if an October/November split is needed.", ""]
    lines += ["Wait for the researcher's explicit OK before the full run. Direction 2 remains a planned follow-up.", ""]
    (root / "report.md").write_text("\n".join(lines))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
