# Full-run scores and paired confidence intervals

24000/24000 observations; complete: True.

Each complete cell contains 200 original items × 5 operational runs. The primary required-call endpoint contains 180 original items; repeated schedules are not independent new questions.

| Model | Precision | Decoder | Observed / planned | All-case accuracy [95% CI] | Required-call accuracy [95% CI] |
| --- | --- | --- | ---: | --- | --- |
| Qwen/Qwen3-0.6B | F16 | free | 1000/1000 | 72.5% [66.5, 78.5] | 73.9% [67.2, 80.0] |
| Qwen/Qwen3-0.6B | F16 | loose | 1000/1000 | 72.5% [66.5, 78.5] | 73.9% [67.2, 80.0] |
| Qwen/Qwen3-0.6B | F16 | trigger_strict | 1000/1000 | 75.0% [69.0, 80.5] | 76.7% [70.0, 82.8] |
| Qwen/Qwen3-0.6B | F16 | whole_strict | 1000/1000 | 75.0% [69.0, 80.5] | 76.7% [70.0, 82.8] |
| Qwen/Qwen3-0.6B | Q4_K_M | free | 1000/1000 | 68.6% [62.1, 74.9] | 70.7% [64.0, 77.0] |
| Qwen/Qwen3-0.6B | Q4_K_M | loose | 1000/1000 | 68.6% [62.2, 74.9] | 70.7% [63.9, 77.0] |
| Qwen/Qwen3-0.6B | Q4_K_M | trigger_strict | 1000/1000 | 72.3% [66.0, 78.3] | 74.8% [68.4, 80.7] |
| Qwen/Qwen3-0.6B | Q4_K_M | whole_strict | 1000/1000 | 73.0% [66.9, 79.0] | 75.6% [69.2, 81.4] |
| meta-llama/Llama-3.2-1B-Instruct | F16 | free | 1000/1000 | 12.0% [7.5, 16.5] | 12.8% [8.3, 17.8] |
| meta-llama/Llama-3.2-1B-Instruct | F16 | loose | 1000/1000 | 12.0% [7.5, 16.5] | 12.8% [8.3, 17.8] |
| meta-llama/Llama-3.2-1B-Instruct | F16 | trigger_strict | 1000/1000 | 48.9% [42.0, 55.7] | 54.3% [47.1, 61.7] |
| meta-llama/Llama-3.2-1B-Instruct | F16 | whole_strict | 1000/1000 | 50.3% [43.4, 57.2] | 55.9% [48.7, 63.1] |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | free | 1000/1000 | 12.9% [8.5, 17.7] | 14.2% [9.3, 19.4] |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | loose | 1000/1000 | 12.7% [8.2, 17.5] | 14.1% [9.2, 19.4] |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | trigger_strict | 1000/1000 | 46.7% [39.7, 53.7] | 51.9% [44.7, 59.1] |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | whole_strict | 1000/1000 | 47.4% [40.5, 54.2] | 52.7% [45.3, 59.9] |
| meta-llama/Llama-3.2-3B-Instruct | F16 | free | 1000/1000 | 25.5% [19.5, 32.0] | 27.2% [20.6, 33.9] |
| meta-llama/Llama-3.2-3B-Instruct | F16 | loose | 1000/1000 | 25.5% [19.5, 32.0] | 27.2% [20.6, 33.9] |
| meta-llama/Llama-3.2-3B-Instruct | F16 | trigger_strict | 1000/1000 | 55.5% [48.5, 62.5] | 61.1% [53.9, 68.3] |
| meta-llama/Llama-3.2-3B-Instruct | F16 | whole_strict | 1000/1000 | 55.5% [48.5, 62.5] | 61.1% [53.9, 68.3] |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | free | 1000/1000 | 26.9% [20.8, 33.1] | 29.2% [22.7, 35.9] |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | loose | 1000/1000 | 27.1% [21.0, 33.3] | 29.4% [22.8, 36.1] |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | trigger_strict | 1000/1000 | 54.4% [47.5, 61.2] | 60.4% [53.3, 67.6] |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | whole_strict | 1000/1000 | 54.9% [48.0, 61.7] | 61.0% [53.9, 68.1] |

Primary intervals use crossed paired resampling of original items and five operational runs, retaining all conditions/models together. Item-only intervals are also saved as a sensitivity check; neither treats repeated schedules as independent items. Required-call subset is the prespecified primary endpoint; all cases include irrelevance. Status counts, category scores, deterministic diagnostic rates, signed precision losses, net recovery and paired decoder contrasts are in summary.json. A recovery share with nonpositive or unstable free loss is undefined or explicitly flagged; it is not a causal fraction of purely syntactic damage.
