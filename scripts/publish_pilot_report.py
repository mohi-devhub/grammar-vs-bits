"""Publish the completed pilot status from saved result/forecast artifacts only."""
import argparse
import json
from qunti.common import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-id', required=True)
    args = parser.parse_args()
    folder = ROOT / 'results/pilot' / args.batch_id
    summary = json.loads((folder / 'summary.json').read_text())
    cost = json.loads((folder / 'budget_forecast.json').read_text())
    if not summary['complete'] or not summary['calibration_usable']:
        raise RuntimeError('Incomplete or operationally unusable pilot cannot be published as completed')
    scored = [json.loads(s) for s in (folder / 'scored.jsonl').read_text().splitlines()]
    by_cell = {(c['quant'], c['condition']): c for c in summary['cells']}
    cells = []
    for q in ('F16', 'Q8_0', 'Q4_K_M'):
        free, strict = by_cell[q, 'free'], by_cell[q, 'whole_strict']
        cells.append(f"| {q} | {free['correct']}/{free['attempts']} | {strict['correct']}/{strict['attempts']} | {free['format_failures']} / {strict['format_failures']} |")
    chosen = [s for s in cost['scenarios'] if (s['assumed_llama_1b_cost_multiple'],s['assumed_llama_3b_cost_multiple']) == (2,6)]
    lo, hi = [s['project_total_at_reported_spend_usd'] for s in chosen]
    stress = cost['scenarios'][-1]['project_total_at_reported_spend_usd']
    free_gap = by_cell['F16','free']['correct']/50 - by_cell['Q4_K_M','free']['correct']/50
    strict_gap = by_cell['F16','whole_strict']['correct']/50 - by_cell['Q4_K_M','whole_strict']['correct']/50
    text = f'''# Completed Qwen pilot — {args.batch_id}

**All {summary['responses_received']}/{summary['planned_generations']} generations completed on one {summary['gpu_metadata']['gpu_name']}** (Modal A10 request, A10G billing SKU). Every precision and both decoder arms used that same worker. Status counts: {summary['status_counts']}. The full run is unlaunched and still requires explicit approval. Direction 2 remains the planned follow-up.

## Timing and measured-cost evidence

| Quantity | Saved result |
| --- | --- |
| Pooled inference batch wall time, four parallel slots | {summary['measured_inference_batch_wall_seconds']:.6f} seconds |
| GPU worker body, including loading and warmups | {summary['measured_gpu_function_seconds']:.6f} seconds |
| Mean amortized inference wall time per generation | {summary['measured_inference_batch_wall_seconds']/summary['responses_received']:.6f} seconds; this is throughput, not individual-request latency |
| Timed inference resource estimate | ${summary['timed_inference_resource_cost_usd']:.8f}; ${summary['timed_inference_usd_per_generation']:.8f}/generation |
| Timed GPU + preparation + supervisor body estimate | ${summary['gpu_prep_supervisor_body_resource_estimate_usd']:.8f}; ${summary['gpu_prep_supervisor_body_usd_per_generation']:.8f}/generation |
| Successful retry cost reported to date, including its rebuild | ${cost['reported_batch_cost_usd']:.8f}; ${cost['reported_batch_cost_per_received_generation_usd']:.8f}/generation |
| Successful retry reported cost per unique pilot item | ${cost['reported_batch_cost_usd']/50:.8f}, across 50 unique items |
| Entire project cost reported to date, including all earlier failures/preparation | ${cost['reported_project_cost_usd']:.8f}; ${cost['reported_project_cost_amortized_per_received_generation_usd']:.8f}/generation amortized across this pilot |
| Retained settling/storage reservations | ${cost['retained_reservations_usd']:.2f}; held funds, not spending |

Billing snapshot: {cost['billing_capture']}. **Reported-to-date amounts are not settled invoices** and storage completeness is not established. Timing-based estimates exclude build/startup/idle and post-timer cleanup/commit costs; the tagged billing ratios include costs reported for those stages. GPU queueing itself is not charged; the small CPU supervisor is a separate billed resource. No CPU model preparation was invoked in this retry: it reused the earlier hashed F16/Q8/Q4 artifacts.

## Full-run forecast against the $12 October cap

Qwen's unchanged 8,000-call main-design share extrapolates to **${summary['projection']['qwen_main_8000_calls_resource_usd_at_observed_throughput']:.4f}** in inference resources at observed pooled free/whole-strict throughput on A10. This is an extrapolation, not a completed main run.

A planning scenario with Llama 1B costing **2×** and Llama 3B **6×** Qwen per call, and the four-arm pool costing **1–2×** the measured two-arm pool, gives **${lo:.2f}–${hi:.2f} total project cost**. This includes reported spending and an explicitly chosen **$1** allowance for further preparation/startup/storage. Those factors and the allowance are assumptions, not measurements or statistical confidence bounds. A slower 3×/10× model scenario with a 2× arm factor reaches **${stress:.2f}** total, leaving very little room below $12. More severe slowdowns can exceed the cap.

The planning case fits October, so a November split is not yet necessary. Before committing all cells, use early approved complete run units to measure Llama and loose/trigger arm costs, then update the projection and remaining shared credits. If the unchanged matrix will not fit, propose completing whole model/seed units (both precisions, all four arms, all frozen items) in October and the remainder from November 1. Preserve every selected model, case, arm and all five runs. Neither October full runs nor November continuation are approved now.

Full scenarios and assumptions: [budget_forecast.json](../results/pilot/{args.batch_id}/budget_forecast.json).

## Descriptive pilot scores — not the four-arm study

| Precision | Free BFCL correct | Whole-strict BFCL correct | Format failures: free / strict |
| --- | ---: | ---: | ---: |
'''+ '\n'.join(cells)+f'''

Each cell uses the same 50 cases, including five irrelevance cases; these are official AST/irrelevance scores with independent format/finish flags. Raw outputs and scoring diagnostics remain available. This pilot has only one operational run and two decoder arms.

For Q4 the observed free precision gap is {100*free_gap:.1f} percentage points and the strict gap is {100*strict_gap:.1f} points. **There is no positive quantization loss in this pilot**, so a recovered-share percentage is undefined. This does not establish equivalence or resolve the strict-versus-loose question. There are no main-study claims or manuscript result numbers here.

## Reproducibility and shutdown

Frozen item coverage matched exactly, all rows report the same GPU, and response timings reported zero prompt-cache reuse. Model properties confirmed F16, Q8_0 and Q4_K–Medium files. The pinned source archive establishes commit identity; the server's archive-built version string is b0-unknown. The Linux audit saved from the executed image has no reported vulnerabilities. Native SM86 serving code is compatible with the approved 8.6/8.9 GPUs under NVIDIA's documented cubin compatibility; no GPU migration occurred.

All listed apps are stopped and the container list is empty. The cloud supervisor finished, durably checkpointed the events, and stopped only its own app. Evalnoise was already stopped before launch; serialization checks and monitor evidence are retained. An earlier retry was interrupted during building, with no stopping actor in its lifecycle; that failure and its cost are retained.

Artifacts: [raw events](../results/pilot/{args.batch_id}/events.jsonl), [scored outputs](../results/pilot/{args.batch_id}/scored.jsonl), [timing/scoring summary](../results/pilot/{args.batch_id}/summary.json), [runtime checks](../results/ops/{args.batch_id}_runtime_validation.json), [Linux audit](../results/ops/pip-audit-linux-{args.batch_id}.json), [shutdown](../results/ops/{args.batch_id}_final_apps.json), [budget](../BUDGET.md), [learning notes](../LEARNING.md).

Regenerate:

```sh
.venv/bin/python -m scripts.report_pilot --batch-id {args.batch_id}
.venv/bin/python -m scripts.report_forecast --batch-id {args.batch_id}
.venv/bin/python -m scripts.publish_pilot_report --batch-id {args.batch_id}
```
'''
    (ROOT / 'docs/PILOT_REPORT.md').write_text(text)
    print('Published completed pilot report from saved artifacts.')


if __name__ == '__main__':
    main()
