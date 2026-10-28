# Qwen pilot report

Generated from `results/pilot/pilot-008/events.jsonl` at 2026-10-27T17:07:30.134432+00:00.

Allocated GPU type: A10. All pilot arms and precisions use the same worker.

300 / 300 planned attempts; 300 returned responses; 300 completed responses. No failed attempt is removed.

| Precision | Decoder | Attempts | BFCL correct | Format failures | Status counts |
| --- | --- | ---: | ---: | ---: | --- |
| F16 | free | 50 | 33 | 0 | {'ok': 50} |
| F16 | whole_strict | 50 | 35 | 0 | {'ok': 50} |
| Q4_K_M | free | 50 | 34 | 2 | {'ok': 50} |
| Q4_K_M | whole_strict | 50 | 36 | 0 | {'ok': 50} |
| Q8_0 | free | 50 | 33 | 0 | {'ok': 50} |
| Q8_0 | whole_strict | 50 | 35 | 0 | {'ok': 50} |

This pilot calibrates runtime and implementation; it does not establish the four-arm, five-run research result.

Measured inference batch wall time: 37.815 seconds. GPU function time (including loading/warmup): 44.850 seconds. CPU preparation function time: 0.000 seconds.

Timing-based inference resource estimate: $0.013893 total; $0.00004631 per attempted request. Preparation plus GPU function resource estimate: $0.016478; $0.00005493 per attempt; $0.000330 per unique item.

These timing estimates exclude platform startup, image builds, idle, post-timer cleanup/volume commits, and persistent storage. Use the separate saved tagged billing report for metered costs; account-wide changes include other projects.

Qwen's 8,000 full-design calls extrapolate to $0.3773 of inference resources **if** both new decoder arms match the pooled free/whole-strict throughput. Llama speed and lazy/permissive-arm output lengths have not been measured.

| Assumed per-Llama cost relative to Qwen | Assumed whole-grid throughput cost multiplier | Full-grid inference USD |
| ---: | ---: | ---: |
| 1 | 1 | 1.1320 |
| 1 | 2 | 2.2640 |
| 3 | 1 | 2.6413 |
| 3 | 2 | 5.2826 |
| 5 | 1 | 4.1506 |
| 5 | 2 | 8.3012 |

Scenario factors are assumptions, not measurements, and exclude further setup/storage costs. This table is not a guaranteed bound or full-run authorization. Preserve all models, arms, and runs if an October/November split is needed.

Wait for the researcher's explicit OK before the full run. Direction 2 remains a planned follow-up.
