# Separate Pythonic call-format sensitivity

Joint prompt/parser/grammar contract sensitivity. Primary comparisons are limited to the identical 60 parallel items. No pooling into the primary 200; no causal attribution to syntax alone.

4800 observations; failures retained. Status counts: {'ok': 4222, 'token_limit': 578}.

| Model | Precision | Decoder | Subset | Accuracy [95% CI] |
| --- | --- | --- | --- | --- |
| meta-llama/Llama-3.2-1B-Instruct | F16 | free | all | 8.3 [4.2, 13.3]% |
| meta-llama/Llama-3.2-1B-Instruct | F16 | whole_strict | all | 55.5 [46.7, 64.2]% |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | free | all | 4.5 [1.3, 8.5]% |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | whole_strict | all | 52.8 [44.2, 61.7]% |
| meta-llama/Llama-3.2-1B-Instruct | F16 | free | parallel | 16.7 [8.3, 26.7]% |
| meta-llama/Llama-3.2-1B-Instruct | F16 | whole_strict | parallel | 68.3 [56.7, 80.0]% |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | free | parallel | 9.0 [3.0, 16.7]% |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | whole_strict | parallel | 62.3 [50.0, 74.3]% |
| meta-llama/Llama-3.2-1B-Instruct | F16 | free | parallel_multiple | 0.0 [0.0, 0.0]% |
| meta-llama/Llama-3.2-1B-Instruct | F16 | whole_strict | parallel_multiple | 42.7 [30.0, 55.0]% |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | free | parallel_multiple | 0.0 [0.0, 0.0]% |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | whole_strict | parallel_multiple | 43.3 [30.0, 55.0]% |
| meta-llama/Llama-3.2-3B-Instruct | F16 | free | all | 0.8 [0.0, 2.5]% |
| meta-llama/Llama-3.2-3B-Instruct | F16 | whole_strict | all | 85.8 [79.2, 91.7]% |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | free | all | 0.8 [0.0, 2.5]% |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | whole_strict | all | 84.7 [78.0, 90.7]% |
| meta-llama/Llama-3.2-3B-Instruct | F16 | free | parallel | 0.0 [0.0, 0.0]% |
| meta-llama/Llama-3.2-3B-Instruct | F16 | whole_strict | parallel | 91.7 [85.0, 98.3]% |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | free | parallel | 0.0 [0.0, 0.0]% |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | whole_strict | parallel | 88.3 [80.0, 95.7]% |
| meta-llama/Llama-3.2-3B-Instruct | F16 | free | parallel_multiple | 1.7 [0.0, 5.0]% |
| meta-llama/Llama-3.2-3B-Instruct | F16 | whole_strict | parallel_multiple | 80.0 [70.0, 90.0]% |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | free | parallel_multiple | 1.7 [0.0, 5.0]% |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | whole_strict | parallel_multiple | 81.0 [70.7, 90.0]% |

## Matched Pythonic-minus-JSON protocol contrasts

| Model | Precision | Decoder | Difference [95% CI], pp |
| --- | --- | --- | --- |
| meta-llama/Llama-3.2-1B-Instruct | F16 | free | 16.7 [8.3, 26.7] |
| meta-llama/Llama-3.2-1B-Instruct | F16 | whole_strict | 66.7 [53.3, 78.3] |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | free | 9.0 [3.0, 16.7] |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | whole_strict | 61.3 [48.7, 73.3] |
| meta-llama/Llama-3.2-3B-Instruct | F16 | free | 0.0 [0.0, 0.0] |
| meta-llama/Llama-3.2-3B-Instruct | F16 | whole_strict | 91.7 [85.0, 98.3] |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | free | 0.0 [0.0, 0.0] |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | whole_strict | 88.3 [80.0, 95.7] |

## Precision interaction

| Model | Subset | Pythonic incremental recovery [95% CI], pp | Change versus JSON [95% CI], pp |
| --- | --- | --- | --- |
| meta-llama/Llama-3.2-1B-Instruct | all | 1.2 [-5.7, 8.0] | No matched JSON cohort |
| meta-llama/Llama-3.2-1B-Instruct | parallel | 1.7 [-10.3, 13.7] | 2.3 [-10.0, 15.0] |
| meta-llama/Llama-3.2-1B-Instruct | parallel_multiple | 0.7 [-6.0, 7.3] | No matched JSON cohort |
| meta-llama/Llama-3.2-3B-Instruct | all | -1.2 [-5.0, 2.7] | No matched JSON cohort |
| meta-llama/Llama-3.2-3B-Instruct | parallel | -3.3 [-8.7, 0.7] | -3.3 [-8.7, 0.7] |
| meta-llama/Llama-3.2-3B-Instruct | parallel_multiple | 1.0 [-4.7, 6.7] | No matched JSON cohort |

## Operational outcomes

| Model | Precision | Decoder | Status counts |
| --- | --- | --- | --- |
| meta-llama/Llama-3.2-1B-Instruct | F16 | free | {'ok': 454, 'token_limit': 146} |
| meta-llama/Llama-3.2-1B-Instruct | F16 | whole_strict | {'ok': 535, 'token_limit': 65} |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | free | {'ok': 316, 'token_limit': 284} |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | whole_strict | {'ok': 536, 'token_limit': 64} |
| meta-llama/Llama-3.2-3B-Instruct | F16 | free | {'ok': 595, 'token_limit': 5} |
| meta-llama/Llama-3.2-3B-Instruct | F16 | whole_strict | {'ok': 595, 'token_limit': 5} |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | free | {'ok': 596, 'token_limit': 4} |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | whole_strict | {'ok': 595, 'token_limit': 5} |

Additional reported app costs: 0.7346155099999999 USD; project reported total: 3.3455842600000008 USD. Caps: $3 additional/$12 project. Metering may lag.

We additionally collected 4,800 responses on 120 frozen cases, using the original parallel subset plus a separately sampled parallel-multiple subset, both Llama models, both precisions, free/whole strict and the same operational labels. The prompt follows Meta call-list syntax, omits the HF tools injection, and uses [] for abstention. Llama-3.2-1B Q4 whole-strict parallel accuracy is 62.3 [50.0, 74.3]%, versus 1.0% under the original JSON contract. Its Pythonic parallel incremental recovery is 1.7 [-10.3, 13.7] points; the paired change in recovery versus JSON is 2.3 [-10.0, 15.0] points; Llama-3.2-3B Q4 whole-strict parallel accuracy is 88.3 [80.0, 95.7]%, versus 0.0% under the original JSON contract. Its Pythonic parallel incremental recovery is -3.3 [-8.7, 0.7] points; the paired change in recovery versus JSON is -3.3 [-8.7, 0.7] points. These gains change the interpretation of the low primary Llama parallel scores: they are strongly contract-dependent, rather than evidence of an intrinsic inability to make parallel calls. Neither parallel incremental recovery nor its protocol change is resolved from zero. This is a joint prompt/parser/grammar sensitivity, not a parser-only causal estimate. Only the original parallel items have a matched primary baseline; parallel-multiple results are reported separately. Sessions differ in time and host, so this is not a randomized crossover. Llama-3B was interrupted by the platform after 1,610 durable outputs; only the missing 790 cells continued on another A10, with saved failures retained. The primary matrix is unchanged. Additional status counts are ok: 4222; token_limit: 578. These limits remain incorrect; no added exclusion analysis is claimed.

Reproduce offline: `.venv/bin/python -m scripts.report_pythonic --run-id pythonic-002`. No generated call is executed. The source JSON primary results are unchanged.
