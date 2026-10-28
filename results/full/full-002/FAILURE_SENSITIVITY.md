# Operational failures and exclusion sensitivity

Post-hoc analysis of saved outputs only. The registered results still count all operational failures as incorrect.

## Failure inventory

Each cell contains 1,000 attempts. Zero rows are retained.

| Model | Precision | Decoder | Token limit | Replay error | Remaining |
| --- | --- | --- | ---: | ---: | ---: |
| Qwen/Qwen3-0.6B | F16 | free | 0 | 0 | 1000 |
| Qwen/Qwen3-0.6B | F16 | loose | 0 | 0 | 1000 |
| Qwen/Qwen3-0.6B | F16 | trigger_strict | 0 | 0 | 1000 |
| Qwen/Qwen3-0.6B | F16 | whole_strict | 0 | 0 | 1000 |
| Qwen/Qwen3-0.6B | Q4_K_M | free | 0 | 0 | 1000 |
| Qwen/Qwen3-0.6B | Q4_K_M | loose | 0 | 0 | 1000 |
| Qwen/Qwen3-0.6B | Q4_K_M | trigger_strict | 0 | 0 | 1000 |
| Qwen/Qwen3-0.6B | Q4_K_M | whole_strict | 0 | 0 | 1000 |
| meta-llama/Llama-3.2-1B-Instruct | F16 | free | 0 | 0 | 1000 |
| meta-llama/Llama-3.2-1B-Instruct | F16 | loose | 0 | 0 | 1000 |
| meta-llama/Llama-3.2-1B-Instruct | F16 | trigger_strict | 24 | 0 | 976 |
| meta-llama/Llama-3.2-1B-Instruct | F16 | whole_strict | 0 | 0 | 1000 |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | free | 9 | 0 | 991 |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | loose | 12 | 0 | 988 |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | trigger_strict | 52 | 1 | 947 |
| meta-llama/Llama-3.2-1B-Instruct | Q4_K_M | whole_strict | 4 | 0 | 996 |
| meta-llama/Llama-3.2-3B-Instruct | F16 | free | 5 | 0 | 995 |
| meta-llama/Llama-3.2-3B-Instruct | F16 | loose | 5 | 0 | 995 |
| meta-llama/Llama-3.2-3B-Instruct | F16 | trigger_strict | 5 | 0 | 995 |
| meta-llama/Llama-3.2-3B-Instruct | F16 | whole_strict | 5 | 0 | 995 |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | free | 5 | 0 | 995 |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | loose | 5 | 0 | 995 |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | trigger_strict | 6 | 0 | 994 |
| meta-llama/Llama-3.2-3B-Instruct | Q4_K_M | whole_strict | 2 | 0 | 998 |

All token-limit runtime combinations (predicted tokens, stop type, configured cap → count): [{"tokens_predicted": 512, "stop_type": "limit", "n_predict": 512, "count": 139}].

Replay identifiers and the exact saved server response are in failure_sensitivity.json. No generation was retried.


## Exclusion rules and uncertainty

All exclusions condition on post-treatment completion. Cell-only exclusion changes comparison populations. Matched exclusions remove healthy counterparts too. None replaces the registered failure-inclusive estimand.

All intervals use crossed original-item/run resampling with the saved seed and replicate count. Repeated schedules are not independent items. Masked bootstrap means renormalize by retained observations in each draw. No zero-denominator draw is silently discarded. Complete-item analysis resamples only retained items. Different model cohorts prevent a cross-model paired interpretation.

### cell_completed

Exclude only failed generations; cell populations differ.
Across the complete matrix: 23860 retained observations; 140 removed, including healthy matched counterparts where required.

| Model | Subset | F16 free / Q4 free / F16 whole / Q4 whole retained |
| --- | --- | --- |
| Qwen/Qwen3-0.6B | all | 1000 / 1000 / 1000 / 1000 |
| Qwen/Qwen3-0.6B | required | 900 / 900 / 900 / 900 |
| meta-llama/Llama-3.2-1B-Instruct | all | 1000 / 991 / 1000 / 996 |
| meta-llama/Llama-3.2-1B-Instruct | required | 900 / 891 / 900 / 896 |
| meta-llama/Llama-3.2-3B-Instruct | all | 995 / 995 / 995 / 998 |
| meta-llama/Llama-3.2-3B-Instruct | required | 895 / 895 / 895 / 898 |

| Model | Subset | Decoder | Primary recovery [95% CI], pp | Excluded recovery [95% CI], pp | Interval interpretation changed? |
| --- | --- | --- | --- | --- | --- |
| Qwen/Qwen3-0.6B | all | loose | 0.00 [-1.20, 1.40] | 0.00 [-1.20, 1.40] | False |
| Qwen/Qwen3-0.6B | all | trigger_strict | 1.20 [-1.40, 3.80] | 1.20 [-1.40, 3.80] | False |
| Qwen/Qwen3-0.6B | all | whole_strict | 1.90 [-0.60, 4.50] | 1.90 [-0.60, 4.50] | False |
| Qwen/Qwen3-0.6B | required | loose | 0.00 [-1.33, 1.44] | 0.00 [-1.33, 1.44] | False |
| Qwen/Qwen3-0.6B | required | trigger_strict | 1.33 [-1.56, 4.33] | 1.33 [-1.56, 4.33] | False |
| Qwen/Qwen3-0.6B | required | whole_strict | 2.11 [-0.67, 5.22] | 2.11 [-0.67, 5.22] | False |
| meta-llama/Llama-3.2-1B-Instruct | all | loose | -0.20 [-1.00, 0.30] | -0.16 [-0.98, 0.37] | False |
| meta-llama/Llama-3.2-1B-Instruct | all | trigger_strict | -3.10 [-7.10, 0.80] | -1.81 [-6.19, 2.53] | False |
| meta-llama/Llama-3.2-1B-Instruct | all | whole_strict | -3.80 [-7.90, 0.20] | -3.73 [-7.79, 0.28] | False |
| meta-llama/Llama-3.2-1B-Instruct | required | loose | -0.11 [-0.89, 0.33] | -0.06 [-0.86, 0.43] | False |
| meta-llama/Llama-3.2-1B-Instruct | required | trigger_strict | -3.89 [-8.33, 0.22] | -2.22 [-7.09, 2.49] | False |
| meta-llama/Llama-3.2-1B-Instruct | required | whole_strict | -4.67 [-9.11, -0.33] | -4.58 [-9.07, -0.26] | False |
| meta-llama/Llama-3.2-3B-Instruct | all | loose | 0.20 [-0.50, 0.90] | 0.20 [-0.50, 0.90] | False |
| meta-llama/Llama-3.2-3B-Instruct | all | trigger_strict | -2.50 [-5.20, 0.00] | -2.46 [-5.19, 0.10] | False |
| meta-llama/Llama-3.2-3B-Instruct | all | whole_strict | -2.00 [-4.60, 0.50] | -2.18 [-4.84, 0.36] | False |
| meta-llama/Llama-3.2-3B-Instruct | required | loose | 0.22 [-0.33, 1.00] | 0.22 [-0.34, 1.00] | False |
| meta-llama/Llama-3.2-3B-Instruct | required | trigger_strict | -2.67 [-5.56, 0.11] | -2.61 [-5.58, 0.22] | False |
| meta-llama/Llama-3.2-3B-Instruct | required | whole_strict | -2.11 [-5.00, 0.56] | -2.33 [-5.25, 0.44] | False |
### matched_panel

Exclude all eight conditions of a model/item/run if any failed.
Across the complete matrix: 23336 retained observations; 664 removed, including healthy matched counterparts where required.

| Model | Subset | F16 free / Q4 free / F16 whole / Q4 whole retained |
| --- | --- | --- |
| Qwen/Qwen3-0.6B | all | 1000 / 1000 / 1000 / 1000 |
| Qwen/Qwen3-0.6B | required | 900 / 900 / 900 / 900 |
| meta-llama/Llama-3.2-1B-Instruct | all | 929 / 929 / 929 / 929 |
| meta-llama/Llama-3.2-1B-Instruct | required | 834 / 834 / 834 / 834 |
| meta-llama/Llama-3.2-3B-Instruct | all | 988 / 988 / 988 / 988 |
| meta-llama/Llama-3.2-3B-Instruct | required | 888 / 888 / 888 / 888 |

| Model | Subset | Decoder | Primary recovery [95% CI], pp | Excluded recovery [95% CI], pp | Interval interpretation changed? |
| --- | --- | --- | --- | --- | --- |
| Qwen/Qwen3-0.6B | all | loose | 0.00 [-1.20, 1.40] | 0.00 [-1.20, 1.40] | False |
| Qwen/Qwen3-0.6B | all | trigger_strict | 1.20 [-1.40, 3.80] | 1.20 [-1.40, 3.80] | False |
| Qwen/Qwen3-0.6B | all | whole_strict | 1.90 [-0.60, 4.50] | 1.90 [-0.60, 4.50] | False |
| Qwen/Qwen3-0.6B | required | loose | 0.00 [-1.33, 1.44] | 0.00 [-1.33, 1.44] | False |
| Qwen/Qwen3-0.6B | required | trigger_strict | 1.33 [-1.56, 4.33] | 1.33 [-1.56, 4.33] | False |
| Qwen/Qwen3-0.6B | required | whole_strict | 2.11 [-0.67, 5.22] | 2.11 [-0.67, 5.22] | False |
| meta-llama/Llama-3.2-1B-Instruct | all | loose | -0.20 [-1.00, 0.30] | -0.11 [-0.85, 0.34] | False |
| meta-llama/Llama-3.2-1B-Instruct | all | trigger_strict | -3.10 [-7.10, 0.80] | -2.58 [-6.69, 1.45] | False |
| meta-llama/Llama-3.2-1B-Instruct | all | whole_strict | -3.80 [-7.90, 0.20] | -3.77 [-7.99, 0.32] | False |
| meta-llama/Llama-3.2-1B-Instruct | required | loose | -0.11 [-0.89, 0.33] | -0.12 [-0.95, 0.37] | False |
| meta-llama/Llama-3.2-1B-Instruct | required | trigger_strict | -3.89 [-8.33, 0.22] | -3.48 [-8.03, 0.74] | False |
| meta-llama/Llama-3.2-1B-Instruct | required | whole_strict | -4.67 [-9.11, -0.33] | -4.80 [-9.39, -0.48] | False |
| meta-llama/Llama-3.2-3B-Instruct | all | loose | 0.20 [-0.50, 0.90] | 0.20 [-0.50, 0.91] | False |
| meta-llama/Llama-3.2-3B-Instruct | all | trigger_strict | -2.50 [-5.20, 0.00] | -2.53 [-5.25, 0.00] | False |
| meta-llama/Llama-3.2-3B-Instruct | all | whole_strict | -2.00 [-4.60, 0.50] | -2.02 [-4.67, 0.50] | False |
| meta-llama/Llama-3.2-3B-Instruct | required | loose | 0.22 [-0.33, 1.00] | 0.23 [-0.34, 1.01] | False |
| meta-llama/Llama-3.2-3B-Instruct | required | trigger_strict | -2.67 [-5.56, 0.11] | -2.70 [-5.65, 0.11] | False |
| meta-llama/Llama-3.2-3B-Instruct | required | whole_strict | -2.11 [-5.00, 0.56] | -2.14 [-5.09, 0.57] | False |
### complete_item

Exclude an original item from all conditions/runs if any failed.
Across the complete matrix: 23200 retained observations; 800 removed, including healthy matched counterparts where required.

| Model | Subset | F16 free / Q4 free / F16 whole / Q4 whole retained |
| --- | --- | --- |
| Qwen/Qwen3-0.6B | all | 1000 / 1000 / 1000 / 1000 |
| Qwen/Qwen3-0.6B | required | 900 / 900 / 900 / 900 |
| meta-llama/Llama-3.2-1B-Instruct | all | 915 / 915 / 915 / 915 |
| meta-llama/Llama-3.2-1B-Instruct | required | 820 / 820 / 820 / 820 |
| meta-llama/Llama-3.2-3B-Instruct | all | 985 / 985 / 985 / 985 |
| meta-llama/Llama-3.2-3B-Instruct | required | 885 / 885 / 885 / 885 |

| Model | Subset | Decoder | Primary recovery [95% CI], pp | Excluded recovery [95% CI], pp | Interval interpretation changed? |
| --- | --- | --- | --- | --- | --- |
| Qwen/Qwen3-0.6B | all | loose | 0.00 [-1.20, 1.40] | 0.00 [-1.20, 1.40] | False |
| Qwen/Qwen3-0.6B | all | trigger_strict | 1.20 [-1.40, 3.80] | 1.20 [-1.40, 3.80] | False |
| Qwen/Qwen3-0.6B | all | whole_strict | 1.90 [-0.60, 4.50] | 1.90 [-0.60, 4.50] | False |
| Qwen/Qwen3-0.6B | required | loose | 0.00 [-1.33, 1.44] | 0.00 [-1.33, 1.44] | False |
| Qwen/Qwen3-0.6B | required | trigger_strict | 1.33 [-1.56, 4.33] | 1.33 [-1.56, 4.33] | False |
| Qwen/Qwen3-0.6B | required | whole_strict | 2.11 [-0.67, 5.22] | 2.11 [-0.67, 5.22] | False |
| meta-llama/Llama-3.2-1B-Instruct | all | loose | -0.20 [-1.00, 0.30] | -0.11 [-0.87, 0.33] | False |
| meta-llama/Llama-3.2-1B-Instruct | all | trigger_strict | -3.10 [-7.10, 0.80] | -2.51 [-6.78, 1.53] | False |
| meta-llama/Llama-3.2-1B-Instruct | all | whole_strict | -3.80 [-7.90, 0.20] | -3.83 [-8.20, 0.33] | False |
| meta-llama/Llama-3.2-1B-Instruct | required | loose | -0.11 [-0.89, 0.33] | -0.12 [-0.98, 0.37] | False |
| meta-llama/Llama-3.2-1B-Instruct | required | trigger_strict | -3.89 [-8.33, 0.22] | -3.41 [-7.93, 0.85] | False |
| meta-llama/Llama-3.2-1B-Instruct | required | whole_strict | -4.67 [-9.11, -0.33] | -4.88 [-9.51, -0.49] | False |
| meta-llama/Llama-3.2-3B-Instruct | all | loose | 0.20 [-0.50, 0.90] | 0.20 [-0.51, 0.91] | False |
| meta-llama/Llama-3.2-3B-Instruct | all | trigger_strict | -2.50 [-5.20, 0.00] | -2.54 [-5.28, 0.00] | False |
| meta-llama/Llama-3.2-3B-Instruct | all | whole_strict | -2.00 [-4.60, 0.50] | -2.03 [-4.67, 0.41] | False |
| meta-llama/Llama-3.2-3B-Instruct | required | loose | 0.22 [-0.33, 1.00] | 0.23 [-0.45, 1.02] | False |
| meta-llama/Llama-3.2-3B-Instruct | required | trigger_strict | -2.67 [-5.56, 0.11] | -2.71 [-5.76, 0.00] | False |
| meta-llama/Llama-3.2-3B-Instruct | required | whole_strict | -2.11 [-5.00, 0.56] | -2.15 [-5.08, 0.56] | False |

## Does interpretation change?

Directional interval classifications changed in 0/54 recovery effects and 0/36 decoder contrasts across these rules and both endpoints. Numerical bounds within 1e-12 accuracy units of zero count as zero, avoiding a spurious conclusion from floating-point round-off.

Among 9 method/model combinations for required-call whole-strict recovery, 6 have nonpositive observed free loss and 0 have a stable positive bootstrap denominator. The failure-inclusive analysis remains primary.


## Reproduce without cloud work

```sh
.venv/bin/python -m scripts.report_failure_sensitivity --run-id full-002
```

Full cell accuracies, signed losses, recovery shares, decoder contrasts, run denominators, failed-item IDs and raw replay details are in failure_sensitivity.json. Primary raw/scored files are hashed and left unchanged.
