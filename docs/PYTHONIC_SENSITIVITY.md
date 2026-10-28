# Separate Pythonic contract sensitivity

This approved follow-up addresses H1 in AUDIT.md. It is separate from the primary full-002 matrix and from the planned Direction 2 solution study. It tests a different joint prompt, parser and grammar contract, rather than estimating a parser-only causal effect.

The authoritative cohort is data/pythonic/manifest.json and frozen.jsonl: the original 60 parallel items plus 60 parallel_multiple items sampled deterministically from the pinned BFCL v4 pool. Neither selection uses model outputs or baseline success. The request bundles contain the rendered prompts and whole-strict grammars. There are two Llama models, F16 and Q4_K_M, free and whole-strict decoding, and the same five operational labels as the primary study. Every incomplete response counts as incorrect.

The response convention is Meta's documented Pythonic list of keyword-argument calls. Instructions are paraphrased, and [] for abstention is our explicit convention. We omit the HF tools argument to avoid injecting the conflicting single-object JSON instruction. The parser inspects Python ASTs and literal arguments without executing a generated call. The unchanged official BFCL AST checker decides correctness. The grammar is generated from offered tool schemas without consulting reference calls or values.

The executed configs/pythonic_protocol.json inherited unused primary-study models, category_counts and pilot bookkeeping fields. The controller takes its two-model roster from the sensitivity manifest and the actual items from its frozen file; the retained protocol fields do not select Qwen or primary nonparallel cases. Raw per-item coverage and the separate report verify the executed 4,800-cell design. These inherited fields are preserved to maintain the protocol hash recorded by the workers.

Only the original parallel cases have identical primary questions and answers. Paired protocol contrasts use those cases and operational labels. The additional parallel_multiple cases have no primary JSON baseline. Sessions differ in time and physical host, so this is not a randomized crossover. Accuracy gains alone do not establish quantization-specific recovery: the report also subtracts the matched F16 decoder effect.

All jobs use detached spawning on A10 with a 30-minute queue limit, bounded resource envelopes, a $3 additional cap inside the $12 project cap, and the October cutoff. Apps stop after each model. A startup import failure produced no predictions and remains in the cost record. Raw outputs and metering are under results/sensitivity/; executed worker snapshots are under provenance/.

Rebuild the complete saved analysis without model inference:

```sh
.venv/bin/python -m scripts.report_pythonic --run-id pythonic-002
```

The command uses the saved billing snapshot. Its --refresh-billing option queries live metering and is unnecessary for offline reproduction. State files retain the metering available when each controller completed; summary.json gives the later project-wide snapshot including the failed startup. Missing metering rows are unknown, rather than zero.

## Retained platform interruption

Modal aborted the initial Llama-3B worker with an internal-failure message that lists preemption as an example; the exact cause is unconfirmed. Both saved checkpoints contain the same 1,610 outputs. Only the 790 keys without a durable prediction are continued, using another A10 with identical experimental inputs. Existing token limits and other recorded failed responses are never retried. The pre-interruption state and both source checkpoints remain separate. The report combines disjoint keys only after verifying complete coverage and matching weight, prompt, schema and grammar hashes.

This continuation changes worker/slot history within the Llama-3B Q4 block. It is an additional operational limitation. Missing in-flight work may have been billed without producing a durable prediction; it is not fabricated as a scored outcome. The budget includes the interrupted app.
