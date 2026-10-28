"""Reserve budget, launch only the authorized pilot, and stop its app."""
import argparse
import fcntl
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from qunti.common import ROOT, digest, now, read_jsonl, write_json
from qunti.grammar import normalize


def requests_for_pilot():
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer
    protocol = json.loads((ROOT / "configs/protocol.json").read_text())
    local = snapshot_download(protocol["pilot"]["model"], revision="c1899de289a04d12100db370d81485cdf75e47ca",
                              allow_patterns=["tokenizer*.json", "tokenizer*.jinja", "chat_template*.jinja", "config.json"],
                              local_dir=str(ROOT / ".cache/pilot-tokenizer"))
    tokenizer = AutoTokenizer.from_pretrained(local, trust_remote_code=False)
    ids = set(json.loads((ROOT / "data/pilot_ids.json").read_text()))
    out = []
    for item in read_jsonl(ROOT / "data/frozen.jsonl"):
        if item["id"] not in ids:
            continue
        tools = [{"type": "function", "function": {**t, "parameters": normalize(t["parameters"])}} for t in item["input"]["function"]]
        system = ("You are a tool-calling assistant. Use only the offered functions and documented arguments. "
                  "When one or more tools apply, output each call as <tool_call>{\"name\":\"function_name\",\"arguments\":{...}}</tool_call>. "
                  "You may emit multiple such blocks when the request needs multiple calls. "
                  "If none applies, output exactly NO_CALL. Do not add prose, markdown, or reasoning.")
        messages = [{"role": "system", "content": system}] + item["input"]["question"][0]
        prompt = tokenizer.apply_chat_template(messages, tools=tools, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        grammar = (ROOT / "data/grammars/qwen/whole_strict" / (item["id"] + ".gbnf")).read_text()
        out.append({"id": item["id"], "category": item["category"], "prompt": prompt,
                    "input_sha256": item["input_sha256"], "schema_sha256": digest(tools), "grammar": grammar})
    assert len(out) == 50
    write_json(ROOT / "results/ops/pilot_requests.json", out)
    write_json(ROOT / "results/ops/tokenizer.json", {"model": protocol["pilot"]["model"], "revision": "c1899de289a04d12100db370d81485cdf75e47ca",
               "chat_template_sha256": digest(tokenizer.chat_template), "enable_thinking": False,
               "request_count": len(out), "prompt_bytes_sha256": digest([x["prompt"] for x in out])})
    return out


def reserve(batch_id):
    path = ROOT / "results/budget_ledger.json"
    with (ROOT / ".cache/budget.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ledger = json.loads(path.read_text()) if path.exists() else {"october_cap_usd": 12.0, "batches": []}
        if any(b["id"] == batch_id for b in ledger["batches"]):
            raise RuntimeError("Pilot already reserved; reconcile it before retrying")
        reservation = 2.50
        if reservation > 5 or sum(b["reservation_usd"] for b in ledger["batches"]) + reservation > 12:
            raise RuntimeError("Budget reservation rejected")
        ledger["batches"].append({"id": batch_id, "reserved_at": now(), "reservation_usd": reservation,
                                  "status": "reserved", "invoice_cost_usd": None,
                                  "includes": "CPU image build/model preparation, bounded GPU pilot/startup, and storage allowance"})
        write_json(path, ledger)


def billing_snapshot(name):
    for kind, args in [("summary", ["summary", "--for", "2026-10", "--json"]),
                       ("tagged", ["report", "--for", "today", "--tag-names", "project,stage", "--show-resources", "--json"])]:
        result = subprocess.run([str(ROOT / ".venv/bin/modal"), "billing", *args], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            try:
                write_json(ROOT / f"results/ops/{name}_{kind}.json", json.loads(result.stdout))
            except json.JSONDecodeError:
                pass


def freeze_worker_source(batch_id):
    if not batch_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in batch_id):
        raise ValueError("Batch ID must contain only letters, numbers, underscores or hyphens")
    target = ROOT / ".cache/pilot-snapshots" / batch_id / "qunti"
    if target.exists():
        raise RuntimeError("Worker snapshot already exists: use a new explicit batch ID")
    shutil.copytree(ROOT / "qunti", target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    hashes = {str(p.relative_to(target)): digest(p.read_bytes()) for p in target.rglob("*.py")}
    write_json(ROOT / f"results/ops/{batch_id}_worker_source.json", {"date": now(), "sha256": hashes})
    os.environ["QUNTI_WORKER_SOURCE"] = str(target)


def active_evalnoise(apps,allow_concurrent_studies=False):
    from qunti.interlock import blocking_evalnoise
    return blocking_evalnoise(apps,allow_concurrent_studies)


def app_snapshot():
    response = subprocess.run([str(ROOT / ".venv/bin/modal"), "app", "list", "--json", "--limit", "0"],
                              capture_output=True, text=True, check=True, timeout=30)
    return json.loads(response.stdout)


def wait_for_evalnoise(batch_id,allow_concurrent_studies=False):
    while True:
        apps = app_snapshot()
        write_json(ROOT / f"results/ops/{batch_id}_serialization_check.json", {"date": now(), "apps": apps})
        busy = active_evalnoise(apps,allow_concurrent_studies)
        if not busy:
            return
        print("Waiting for active evalnoise app(s): " + ", ".join(a["app_id"] for a in busy), flush=True)
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--batch-id", default="pilot-001")
    parser.add_argument("--reuse-model-artifacts", action="store_true",
                        help="Reuse the saved Qwen artifact manifest and existing project volume; no CPU preparation call")
    parser.add_argument("--queue-wait-seconds", type=int, default=1800)
    args = parser.parse_args()
    if not 1 <= args.queue_wait_seconds <= 1800:
        raise ValueError("Queue wait must be between 1 and 1800 seconds")
    protocol = json.loads((ROOT / "configs/protocol.json").read_text())
    validation = json.loads((ROOT / "results/offline/grammar_validation.json").read_text())
    if validation["failed"]:
        raise RuntimeError("Offline grammar validation must pass before cloud work")
    audit = json.loads((ROOT / "results/ops/pip-audit-local.json").read_text())
    if any(d.get("vulns") for d in audit["dependencies"]):
        raise RuntimeError("Local pip-audit must be clean")
    batch_requests = requests_for_pilot()
    if args.prepare_only:
        print("Prepared 50 fixed prompts. No cloud work launched.")
        return
    if shutil.disk_usage(ROOT).free < 256 * 1024**2:
        raise RuntimeError("Need at least 256 MiB free local disk before paid pilot and raw-result capture")
    wait_for_evalnoise(args.batch_id)
    reserve(args.batch_id)
    billing_snapshot(args.batch_id + "_before")
    freeze_worker_source(args.batch_id)
    import modal
    from cloud import app, prepare_qwen, run_pilot, supervise_pilot
    started = time.monotonic()
    app_id = None
    queue_timer = None
    submitted_at = None
    queue_started = None
    gpu_started = threading.Event()
    monitor_stop = threading.Event()
    monitor = None
    try:
        with modal.enable_output():
            wait_for_evalnoise(args.batch_id)
            with app.run(detach=True):
                app_id = app.app_id
                app.set_tags({"project": "qunti-check", "stage": "pilot", "batch": args.batch_id})
                write_json(ROOT / ("results/ops/" + args.batch_id + "_app.json"), {"app_id": app_id, "started_at": now(), "tags": {"project": "qunti-check", "stage": "pilot", "batch": args.batch_id}})
                if args.reuse_model_artifacts:
                    metadata = json.loads((ROOT / "results/ops/model_artifacts.json").read_text())
                    if metadata["model"] != protocol["pilot"]["model"] or metadata["revision"] != "c1899de289a04d12100db370d81485cdf75e47ca":
                        raise ValueError("Saved artifact manifest does not match the pinned pilot model")
                    if set(metadata["artifacts"]) != set(protocol["pilot"]["precisions"]):
                        raise ValueError("Saved artifact precision set does not match pilot")
                    metadata = {**metadata, "original_preparation_function_seconds": metadata.get("original_preparation_function_seconds", metadata["active_function_seconds"]),
                                "active_function_seconds": 0.0, "artifact_reused": True,
                                "timing_scope": "No CPU preparation function invoked in this batch; original preparation time retained separately"}
                else:
                    metadata = prepare_qwen.remote()
                write_json(ROOT / "results/ops/model_artifacts.json", metadata)
                write_json(ROOT / f"results/ops/{args.batch_id}_model_artifacts.json", metadata)
                write_json(ROOT / f"results/ops/{args.batch_id}_rates.json",
                           json.loads((ROOT / "results/ops/rates-retry.json").read_text()))
                wait_for_evalnoise(args.batch_id)
                def monitor_evalnoise():
                    while not monitor_stop.wait(15):
                        try:
                            busy = active_evalnoise(app_snapshot())
                        except Exception:
                            busy = [{"app_id": "status_check_failed"}]
                        if busy:
                            try:
                                write_json(ROOT / f"results/ops/{args.batch_id}_evalnoise_interlock.json",
                                           {"date": now(), "busy": busy, "action": "Stop our app; never stop evalnoise"})
                            finally:
                                subprocess.run([str(ROOT / ".venv/bin/modal"), "app", "stop", app_id, "--yes"],
                                               capture_output=True, text=True, timeout=60)
                            return
                monitor = threading.Thread(target=monitor_evalnoise, daemon=True)
                monitor.start()
                def stop_if_still_waiting():
                    if not gpu_started.is_set():
                        try:
                            write_json(ROOT / f"results/ops/{args.batch_id}_queue_timeout.json",
                                       {"date": now(), "app_id": app_id, "queue_wait_limit_seconds": args.queue_wait_seconds,
                                        "reason": "No GPU session-start event before bounded wait; stopping app"})
                        finally:
                            subprocess.run([str(ROOT / ".venv/bin/modal"), "app", "stop", app_id, "--yes"],
                                           capture_output=True, text=True, timeout=60)
                queue_timer = threading.Timer(args.queue_wait_seconds, stop_if_still_waiting)
                queue_timer.daemon = True
                submitted_at = now()
                queue_started = time.monotonic()
                path = ROOT / ("results/pilot/" + args.batch_id + "/events.jsonl")
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("w") as f:
                    count = 0
                    gpu_finished = False
                    try:
                        for event in supervise_pilot.remote_gen(batch_requests, protocol, metadata, app_id, args.batch_id):
                            if event["kind"] == "supervisor_ready":
                                queue_timer.start()
                            if event["kind"] == "session_finished":
                                gpu_finished = True
                            if event["kind"] == "session_started":
                                if gpu_started.is_set():
                                    raise RuntimeError("Refusing a second GPU session within one pilot run")
                                gpu_started.set()
                                queue_timer.cancel()
                                write_json(ROOT / f"results/ops/{args.batch_id}_queue_timing.json",
                                           {"submitted_at": submitted_at, "first_gpu_event_received_at": now(),
                                            "client_wait_to_first_gpu_event_seconds": time.monotonic() - queue_started,
                                            "scope": "Includes queue, container startup and RPC; not a measure of billed occupancy",
                                            "hardware": event["metadata"]})
                            f.write(json.dumps(event, ensure_ascii=False) + "\n"); f.flush()
                            if event["kind"] == "generation":
                                count += 1
                                if count % 25 == 0:
                                    print(f"Pilot attempts received: {count}/300", flush=True)
                            else:
                                print("Pilot event: " + event["kind"], flush=True)
                    except Exception as exc:
                        write_json(ROOT / f"results/ops/{args.batch_id}_stream_ending.json",
                                   {"date": now(), "exception_type": type(exc).__name__, "gpu_session_finished": gpu_finished,
                                    "received_generations": count, "note": "Cloud supervisor self-stops its app after durable checkpoint"})
                        if count != 300 or not gpu_finished:
                            raise
                        print("All 300 outputs and GPU completion received before app shutdown.", flush=True)

    finally:
        if queue_timer:
            queue_timer.cancel()
        monitor_stop.set()
        app_id = app_id or app.app_id
        if app_id:
            subprocess.run([str(ROOT / ".venv/bin/modal"), "app", "stop", app_id, "--yes"], check=False, capture_output=True, text=True, timeout=60)
        billing_snapshot(args.batch_id + "_after")
        write_json(ROOT / ("results/ops/" + args.batch_id + "_client_timing.json"), {"date": now(), "client_session_seconds": time.monotonic() - started,
                   "billing_is_separate_from_client_wall_time": True, "app_id": app_id})
        result = subprocess.run([str(ROOT / ".venv/bin/modal"), "app", "list", "--json", "--limit", "0"], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            write_json(ROOT / ("results/ops/" + args.batch_id + "_shutdown.json"), {"date": now(), "apps": json.loads(result.stdout), "stopped_project_app": app_id})


if __name__ == "__main__":
    main()
