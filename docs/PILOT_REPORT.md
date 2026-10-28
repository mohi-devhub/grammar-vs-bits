# Completed Qwen pilot — pilot-008

**All 300/300 generations completed on one NVIDIA A10** (Modal A10 request, A10G billing SKU). Every precision and both decoder arms used that same worker. Status counts: {'ok': 300}. The full run is unlaunched and still requires explicit approval. Direction 2 remains the planned follow-up.

## Timing and measured-cost evidence

| Quantity | Saved result |
| --- | --- |
| Pooled inference batch wall time, four parallel slots | 37.814643 seconds |
| GPU worker body, including loading and warmups | 44.850405 seconds |
| Mean amortized inference wall time per generation | 0.126049 seconds; this is throughput, not individual-request latency |
| Timed inference resource estimate | $0.01389268; $0.00004631/generation |
| Timed GPU + preparation + supervisor body estimate | $0.01674650; $0.00005582/generation |
| Successful retry cost reported to date, including its rebuild | $0.07961645; $0.00026539/generation |
| Successful retry reported cost per unique pilot item | $0.00159233, across 50 unique items |
| Entire project cost reported to date, including all earlier failures/preparation | $0.34335856; $0.00114453/generation amortized across this pilot |
| Retained settling/storage reservations | $4.00; held funds, not spending |

Billing snapshot: 2026-10-27T17:11:06.202272+00:00. **Reported-to-date amounts are not settled invoices** and storage completeness is not established. Timing-based estimates exclude build/startup/idle and post-timer cleanup/commit costs; the tagged billing ratios include costs reported for those stages. GPU queueing itself is not charged; the small CPU supervisor is a separate billed resource. No CPU model preparation was invoked in this retry: it reused the earlier hashed F16/Q8/Q4 artifacts.

## Full-run forecast against the $12 October cap

Qwen's unchanged 8,000-call main-design share extrapolates to **$0.3773** in inference resources at observed pooled free/whole-strict throughput on A10. This is an extrapolation, not a completed main run.

A planning scenario with Llama 1B costing **2×** and Llama 3B **6×** Qwen per call, and the four-arm pool costing **1–2×** the measured two-arm pool, gives **$4.74–$8.14 total project cost**. This includes reported spending and an explicitly chosen **$1** allowance for further preparation/startup/storage. Those factors and the allowance are assumptions, not measurements or statistical confidence bounds. A slower 3×/10× model scenario with a 2× arm factor reaches **$11.91** total, leaving very little room below $12. More severe slowdowns can exceed the cap.

The planning case fits October, so a November split is not yet necessary. Before committing all cells, use early approved complete run units to measure Llama and loose/trigger arm costs, then update the projection and remaining shared credits. If the unchanged matrix will not fit, propose completing whole model/seed units (both precisions, all four arms, all frozen items) in October and the remainder from November 1. Preserve every selected model, case, arm and all five runs. Neither October full runs nor November continuation are approved now.

Full scenarios and assumptions: [budget_forecast.json](../results/pilot/pilot-008/budget_forecast.json).

## Descriptive pilot scores — not the four-arm study

| Precision | Free BFCL correct | Whole-strict BFCL correct | Format failures: free / strict |
| --- | ---: | ---: | ---: |
| F16 | 33/50 | 35/50 | 0 / 0 |
| Q8_0 | 33/50 | 35/50 | 0 / 0 |
| Q4_K_M | 34/50 | 36/50 | 2 / 0 |

Each cell uses the same 50 cases, including five irrelevance cases; these are official AST/irrelevance scores with independent format/finish flags. Raw outputs and scoring diagnostics remain available. This pilot has only one operational run and two decoder arms.

For Q4 the observed free precision gap is -2.0 percentage points and the strict gap is -2.0 points. **There is no positive quantization loss in this pilot**, so a recovered-share percentage is undefined. This does not establish equivalence or resolve the strict-versus-loose question. There are no main-study claims or manuscript result numbers here.

## Reproducibility and shutdown

Frozen item coverage matched exactly, all rows report the same GPU, and response timings reported zero prompt-cache reuse. Model properties confirmed F16, Q8_0 and Q4_K–Medium files. The pinned source archive establishes commit identity; the server's archive-built version string is b0-unknown. The Linux audit saved from the executed image has no reported vulnerabilities. Native SM86 serving code is compatible with the approved 8.6/8.9 GPUs under NVIDIA's documented cubin compatibility; no GPU migration occurred.

All listed apps are stopped and the container list is empty. The cloud supervisor finished, durably checkpointed the events, and stopped only its own app. Evalnoise was already stopped before launch; serialization checks and monitor evidence are retained. An earlier retry was interrupted during building, with no stopping actor in its lifecycle; that failure and its cost are retained.

Artifacts: [raw events](../results/pilot/pilot-008/events.jsonl), [scored outputs](../results/pilot/pilot-008/scored.jsonl), [timing/scoring summary](../results/pilot/pilot-008/summary.json), [runtime checks](../results/ops/pilot-008_runtime_validation.json), [Linux audit](../results/ops/pip-audit-linux-pilot-008.json), [shutdown](../results/ops/pilot-008_final_apps.json), [budget](../BUDGET.md), [learning notes](../LEARNING.md).

Regenerate:

```sh
.venv/bin/python -m scripts.report_pilot --batch-id pilot-008
.venv/bin/python -m scripts.report_forecast --batch-id pilot-008
.venv/bin/python -m scripts.publish_pilot_report --batch-id pilot-008
```
