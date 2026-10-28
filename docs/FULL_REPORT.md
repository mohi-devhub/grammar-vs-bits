# Full-study report

The matrix frozen before execution is complete: 24,000/24,000 observations. All original items, decoder arms, precisions and operational runs are retained.

[All model × precision × decoder scores and CIs](../results/full/full-002/REPORT.md), [raw/scored result summary](../results/full/full-002/summary.json), [cost accounting](../results/full/full-002/COSTS.md), [integrity checks](../results/full/full-002/integrity.json).

| Model | Q4 free accuracy [95% CI] | Q4 whole-strict accuracy [95% CI] | Incremental recovery [95% CI], points | Share interpretation |
| --- | --- | --- | --- | --- |
| Qwen/Qwen3-0.6B | 70.7% [64.0, 77.0] | 75.6% [69.2, 81.4] | 2.1 percentage points [-0.7, 5.2] | Unstable denominator; no share CI |
| meta-llama/Llama-3.2-1B-Instruct | 14.2% [9.3, 19.4] | 52.7% [45.3, 59.9] | -4.7 percentage points [-9.1, -0.3] | Undefined: nonpositive observed free loss |
| meta-llama/Llama-3.2-3B-Instruct | 29.2% [22.7, 35.9] | 61.0% [53.9, 68.1] | -2.1 percentage points [-5.0, 0.6] | Undefined: nonpositive observed free loss |

The primary campaign snapshot at 2026-10-28T18:57:35.984445+00:00 reports gross project cost $2.610969, against the $12.00 cap, before the separately approved Pythonic follow-up. The original pilot planning range was $4.74–$8.14. Metering can lag; storage completeness is not established. All earlier setup failures and interrupted collections remain in the cost record.

Intervals use crossed paired resampling of original items and operational-run labels. Item-only sensitivity intervals, category endpoints, overlapping diagnostic flags, operational failures and paired decoder contrasts are released. They are pointwise, unadjusted intervals. A positive constrained gain is not a causal partition of syntax and meaning.

The allocation selector stayed A10; the exact device-reported names are retained per item. Within a model, all conditions in the primary matrix share its worker session. Interrupted collections were retained separately and never pooled into the primary comparison. Direction 2 remains planned and unevaluated.

[Failure breakdown and post-hoc exclusion checks](../results/full/full-002/FAILURE_SENSITIVITY.md) report all cells and three exclusion rules. Directional interval classifications change in 0 recovery effects across those rules and both endpoints. These checks condition on completion and leave the primary results frozen before execution unchanged.

At 2026-10-28T18:57:36.704812+00:00, the shutdown snapshot records 0 active project apps and 0 active project containers. Other authorized projects were preserved. [Shutdown evidence](../results/ops/full-002_final_shutdown.json).

## Separate Pythonic format sensitivity

[All additional scores, protocol contrasts and precision interactions](../results/sensitivity/pythonic-002/REPORT.md). These outputs are not pooled into the primary matrix.

| Model | Q4 whole-strict parallel accuracy, JSON → Pythonic | Paired protocol gain [95% CI], points |
| --- | --- | --- |
| meta-llama/Llama-3.2-1B-Instruct | 1.0% → 62.3% [50.0, 74.3] | 61.3 [48.7, 73.3] |
| meta-llama/Llama-3.2-3B-Instruct | 0.0% → 88.3% [80.0, 95.7] | 88.3 [80.0, 95.7] |

meta-llama/Llama-3.2-1B-Instruct: on the same parallel questions, Q4 whole-strict accuracy changes from 1.0% under the original JSON contract to 62.3% [50.0, 74.3] under the Pythonic contract. This changes the serving contract as a whole, rather than isolating a parser-only effect.

meta-llama/Llama-3.2-3B-Instruct: on the same parallel questions, Q4 whole-strict accuracy changes from 0.0% under the original JSON contract to 88.3% [80.0, 95.7] under the Pythonic contract. This changes the serving contract as a whole, rather than isolating a parser-only effect.

Low parallel scores in the original JSON setup should not be treated as an intrinsic limitation of these Llama models. The separate report gives the matched protocol contrasts and their intervals. The original accuracy numbers and their precision interaction remain facts about the original contract.

Additional reported app costs, including the failed setup: 0.7346155099999999 USD. Latest reported project total: 3.3455842600000008 USD. Caps remain $3 additional and $12 total; metering may lag.
