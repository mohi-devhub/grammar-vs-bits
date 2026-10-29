# Sentence changes: editing pass, 2026-10-29

Comparison: the working paper immediately before this editing pass, including its existing method overview figure. Unchanged sentences are omitted. Sentence splits and joins are listed as groups; every removed and added sentence is included. Citation keys and mathematical notation are retained for traceability.

## Author block

Kept M. Mohith and added these two lines:

- Chinmaya Vishwa Vidyapeeth, Kerala, India
- achumohith14@gmail.com (clickable email link)

## Changed sentences

### Abstract

Before:

1. Tool-call format contracts can dominate observed weight-precision gaps in small-model evaluations.
2. On the same 60 parallel cases in a separate sensitivity, Llama-1B Q4 whole-strict parallel accuracy rises from 1.0% to 62.3% (paired gain 61.3 [48.7, 73.3] points); Llama-3B Q4 whole-strict parallel accuracy rises from 0.0% to 88.3% (paired gain 88.3 [80.0, 95.7] points).
3. The observed format-contract gains of 61.3 and 88.3 points are much larger than the corresponding Pythonic F16-to-Q4 whole-strict gaps of 6.0 and 3.3 points.
4. This separate sensitivity changes the prompt, parser and grammar together; it is not a randomized crossover or a parser-only causal effect.
5. Sensitivity parallel incremental recovery and its protocol change remain inconclusive.
6. The primary BFCL conceptual replication remains unchanged; the sensitivity uses Meta's documented Pythonic call-list format with a matching grammar.

After:

1. Does strict grammar decoding recover what Q4 quantization loses in small-model tool calling?
2. We find no clear quantization-specific recovery.
3. Whole-response constraints help F16 at least as much as Q4 for Llama, with nominally negative recovery for Llama-1B.
4. In a separate sensitivity, Meta's Pythonic format and matching grammar raise Q4 whole-strict parallel accuracy from 1.0% to 62.3% for Llama-1B and 0.0% to 88.3% for Llama-3B on the same 60 cases.
5. Paired gains of 61.3 [48.7, 73.3] and 88.3 [80.0, 95.7] points far exceed Pythonic F16-to-Q4 gaps of 6.0 and 3.3 points.
6. A format contract means the prompt, parser and grammar.
7. This nonrandomized sensitivity changes all three, separately from the primary BFCL conceptual replication; it does not isolate a parser-only causal effect.
8. Quantization-specific recovery and its change from JSON remain inconclusive in the sensitivity.

### Introduction, first paragraph

Before:

1. On the same 60 parallel items, the separate sensitivity identifies the serving contract as the larger observed contrast.
2. The observed format-contract gains of 61.3 and 88.3 points are much larger than the corresponding Pythonic F16-to-Q4 whole-strict gaps of 6.0 and 3.3 points.
3. This is a joint prompt/parser/grammar comparison, not a general law about quantization or an intrinsic Llama limitation.

After:

1. Does strict grammar decoding recover tool-calling accuracy lost to Q4 quantization?
2. The primary comparison shows no clear quantization-specific recovery.
3. Whole-response constraints help F16 at least as much as Q4 for Llama, with nominally negative recovery for Llama-1B.
4. Yet Meta's Pythonic format in a separate sensitivity raises Q4 whole-strict accuracy from 1.0% to 62.3% for Llama-1B and 0.0% to 88.3% for Llama-3B on the same 60 parallel cases, far exceeding Pythonic precision gaps of 6.0 and 3.3 points.
5. This changes prompt, parser and grammar together; it establishes neither a general rule about quantization nor an intrinsic Llama limitation.

### Introduction, motivation

Before:

1. Prior work also separates structural and content failures and studies grammar mitigation in quantized models.
2. Our question is narrower: does strict enforcement change the incremental precision gap differently from permissive or trigger-gated grammars?
3. An intervention can improve a quantized model simply because it improves every precision.
4. Conversely, a grammar with an arbitrary-text branch cannot establish a guarantee of schema-valid output.
5. These observations motivate matched full-precision controls and an explicit check of the language each decoder admits.

After:

1. Prior work separates structural and content failures and tests grammar mitigation in quantized models.
2. We ask whether strict enforcement changes the incremental precision gap differently from permissive or trigger-gated grammars.
3. A quantized model can gain simply because an intervention helps every precision.
4. A grammar admitting arbitrary text cannot guarantee schema-valid output.
5. We therefore use matched full-precision controls and check what each decoder admits.

### Frozen tasks and prompts

Before:

1. Original items and accepted answers are shared across conditions; selection does not use model predictions.
2. Prompts are frozen from pinned publisher templates, with a fixed Llama template date.

After:

1. All conditions share original items and accepted answers, selected without model predictions.
2. Prompts are frozen from pinned publisher templates with a fixed Llama template date.

### Precision and hardware records

Before:

1. This reference is an F16 export, not the original checkpoint's possibly different storage dtype.
2. Model revisions, source/output hashes, conversion commands, server arguments and the pinned llama.cpp source [llamacpp] are recorded.
3. All arms and precisions for a model use one A10 worker.
4. The Modal allocation selector is fixed.
5. Device-reported A10/A10G labels and drivers are retained rather than normalized away; model sessions need not share a physical host.

After:

1. The checkpoint's storage dtype may differ from the F16 reference.
2. Model revisions, source and output hashes, conversion commands, server arguments and the pinned llama.cpp source [llamacpp] are recorded.
3. Each model uses one A10 worker for all arms and precisions, with a fixed Modal allocation selector.
4. Records retain device-reported A10/A10G labels and drivers; model sessions may use different physical hosts.

### Decoder prompt contract

Before:

1. Every arm for a given model sees exactly the same rendered prompt and offered tools.
2. Both selected revisions have the same template hash, recorded in Appendix [app:settings].
3. We added a JSON-array convention for parallel calls in the system message, while that HF template inserts a later user-message instruction requesting one JSON object.
4. Meta separately documents a Pythonic list of calls [metaprompt]; our primary JSON contract does not evaluate that format.
5. Llama findings are conditional on this declared contract, rather than claims about its best supported interface.

After:

1. Each model's arms share rendered prompts and offered tools.
2. Both revisions share the template hash in Appendix [app:settings].
3. We added a system-message JSON-array convention for parallel calls, but the HF template's later user-message instruction requests one JSON object.
4. Meta documents Pythonic call lists [metaprompt], which the primary JSON contract does not evaluate.
5. Llama findings concern this declared contract, not its best supported interface.

### Schema compilation

Before:

1. The compiler permits arbitrary ordering of documented object keys while enforcing required/unique keys.
2. Known property sets are closed as an explicit API policy.
3. Free-form dictionaries remain free-form.
4. A nested BFCL dictionary that names required fields without field types retains those names with unconstrained values; types are not guessed from answers.
5. These normalization choices are part of the intervention and are released.

After:

1. The compiler allows documented object keys in any order, requires specified keys and forbids duplicates.
2. As an explicit API policy, known property sets are closed; free-form dictionaries stay free-form.
3. For nested BFCL dictionaries with untyped required fields, names are retained but values are unconstrained; answers never supply types.
4. These normalization choices are released as part of the intervention.

### Grammar validation

Before:

1. Finite character-level membership checks cover the selected schemas, malformed strings, unknown functions, missing/extra arguments, types, key order, parallel calls and abstention.
2. They are evidence of tested coverage, not a proof of every JSON Schema feature or token-level behavior.
3. Separate synthetic runtime probes force a known trigger and verify literal replay and the server's configured lazy mode before benchmark collection.
4. These probes are setup, not benchmark successes.

After:

1. Finite character-level membership checks test selected schemas, malformed strings, unknown functions, missing or extra arguments, types, key order, parallel calls and abstention.
2. These show tested coverage, without proving every JSON Schema feature or token-level behavior.
3. Before collection, synthetic runtime probes force a known trigger to verify literal replay and the server's configured lazy mode.
4. These are setup checks, not benchmark successes.

### Execution

Before:

1. Temperature is zero, with seed/schedule labels frozen before execution and shuffled requests.
2. Identical greedy outputs are retained as operational repeats; they are not new independent items.
3. Configured context/output caps, server slots, cache settings and stop strings match across arms.
4. Llama prompts use publisher token IDs to avoid duplicating the beginning-of-text marker already present in its template.
5. An earlier collection with that duplication is retained as an aborted setup attempt, before task-accuracy inspection.
6. Qwen uses its original string transport with publisher settings that disable added BOS.
7. Cache-reuse timings and actual generation settings are logged.
8. The cloud supervisor checkpoints events, enforces queue/runtime bounds and enforces the scheduling rule frozen before execution.
9. The researcher permitted concurrent full studies after the separate pilots; this does not establish isolated cross-model throughput.

After:

1. Decoding uses temperature zero and shuffled requests, with seed and schedule labels frozen before execution.
2. Identical greedy outputs remain operational repeats, not independent items.
3. Context and output limits, slots, cache settings and stop strings match across arms.
4. Llama uses publisher token IDs to avoid duplicating the template's beginning-of-text marker.
5. An earlier collection with that duplication remains an aborted setup attempt, stopped before accuracy inspection.
6. Qwen prompts remain strings, using publisher settings that disable an added beginning-of-text token.
7. Logs retain cache-reuse timings and actual generation settings.
8. The cloud supervisor checkpoints events and enforces queue, runtime and scheduling limits frozen before execution.
9. The researcher permitted concurrent full studies after separate pilots; cross-model throughput was not isolated.

### Scoring

Before:

1. Official BFCL AST matching is the correctness authority [bfcl].
2. We adapt the declared JSON envelope into calls without executing outputs.
3. The unchanged official irrelevance helper is used through the same parsing adapter.
4. Irrelevance can credit an output with no parsed call while our format diagnostic rejects its prose; those outcomes are reported separately.

After:

1. Official BFCL AST matching determines correctness [bfcl].
2. We parse the declared JSON envelope into calls without executing them.
3. The unchanged official irrelevance helper uses the same parsing adapter.
4. Irrelevance can credit outputs with no parsed call even when our format diagnostic rejects their prose; we report these separately.

### Paired uncertainty

Before:

1. Item-only intervals are saved as a sensitivity check.
2. Intervals are pointwise and unadjusted for multiple comparisons; exploratory contrasts are labeled accordingly.
3. At a boundary with no observed failures, empirical bootstrap intervals can degenerate; this is not a bound on rare unobserved population failures.
4. A recovery-share point estimate $R_d/L_f$ is undefined when observed free loss is nonpositive.
5. Its interval is withheld when bootstrap denominators are unstable; values are not clipped into a manufactured partition.

After:

1. Item-only intervals provide a sensitivity check.
2. Intervals are pointwise and unadjusted for multiple comparisons; exploratory contrasts are labeled.
3. Without observed failures, empirical bootstrap intervals can degenerate and cannot bound rare unobserved population failures.
4. The recovery share $R_d/L_f$ is undefined for nonpositive observed free loss.
5. We withhold its interval when bootstrap denominators are unstable and never clip values into a partition.

### Practical follow-up

Before:

1. The planned Direction 2 follow-up compares schema-audit/precision fallback with ordinary retries; it is not evaluated here.

After:

1. The planned follow-up compares schema-audit and precision-fallback methods with ordinary retries; these methods are not evaluated here.

### Results prose

Before:

1. Qwen3-0.6B: Q4 required-call accuracy changes from 70.7% free to 75.6% whole strict.
2. Across all cases for Qwen3-0.6B, Q4 whole-strict response-structure validity is 100.0 [100.0, 100.0]%, while official accuracy is 73.0 [66.9, 79.0]%.
3. Llama-3.2-1B: Q4 required-call accuracy changes from 14.2% free to 52.7% whole strict.
4. Across all cases for Llama-3.2-1B, Q4 whole-strict response-structure validity is 100.0 [100.0, 100.0]%, while official accuracy is 47.4 [40.5, 54.2]%.
5. Llama-3.2-3B: Q4 required-call accuracy changes from 29.2% free to 61.0% whole strict.
6. Across all cases for Llama-3.2-3B, Q4 whole-strict response-structure validity is 100.0 [100.0, 100.0]%, while official accuracy is 54.9 [48.0, 61.7]%.
7. Generation status counts are grammar_trigger_replay_error: 1; ok: 23860; token_limit: 139.

After:

1. For Qwen3-0.6B, Q4 required-call accuracy rises from 70.7% with free decoding to 75.6% with whole-response constraints.
2. Across all cases, Q4 whole-strict response-structure validity is 100.0 [100.0, 100.0]%, while official accuracy is 73.0 [66.9, 79.0]%.
3. For Llama-3.2-1B, Q4 required-call accuracy rises from 14.2% with free decoding to 52.7% with whole-response constraints.
4. Across all cases, Q4 whole-strict response-structure validity is 100.0 [100.0, 100.0]%, while official accuracy is 47.4 [40.5, 54.2]%.
5. For Llama-3.2-3B, Q4 required-call accuracy rises from 29.2% with free decoding to 61.0% with whole-response constraints.
6. Across all cases, Q4 whole-strict response-structure validity is 100.0 [100.0, 100.0]%, while official accuracy is 54.9 [48.0, 61.7]%.
7. 23,860 generations completed normally, 139 reached the 512-token cap, and one failed during grammar replay.

### Separate format sensitivity

Before:

1. We collected 4,800 responses on 120 cases: the original parallel subset and a separately sampled parallel-multiple subset, both Llama models, both precisions, free/whole strict and the same operational labels.
2. The prompt uses Meta call-list syntax without the HF tools injection, with [] for abstention.
3. Its Pythonic parallel incremental recovery is 1.7 [-10.3, 13.7] points; the paired change in recovery versus JSON is 2.3 [-10.0, 15.0] points; Llama-3.2-3B Q4 whole-strict parallel accuracy is 88.3 [80.0, 95.7]%, versus 0.0% under the original JSON contract.
4. This joint prompt/parser/grammar comparison is matched only on the original parallel items.
5. Llama-3B was interrupted by the platform after 1,610 durable outputs; only the missing 790 cells continued on another A10, with saved failures retained.

After:

1. We collected 4,800 responses on 120 cases: the original parallel and a separately sampled parallel-multiple subset.
2. Both Llama models used both precisions, free and whole-strict decoding, and the same operational labels.
3. The prompt uses Meta's call-list syntax, omits the HF tools instruction and uses [] for abstention.
4. Its Pythonic parallel incremental recovery is 1.7 [-10.3, 13.7] points; the paired change in recovery versus JSON is 2.3 [-10.0, 15.0] points.
5. Llama-3.2-3B Q4 whole-strict parallel accuracy is 88.3 [80.0, 95.7]%, versus 0.0% under the original JSON contract.
6. Only the original parallel items are matched across the changed prompt, parser and grammar.
7. A platform interruption left 1,610 saved Llama-3B outputs.
8. Another A10 collected the remaining 790 responses, retaining all saved failures.

### Costs

Before:

1. The pilot planning scenario for the primary campaign was $4.74--$8.14.
2. Gross tagged project cost reported at the pre-follow-up snapshot is $2.6110, including retained setup and interrupted attempts, against the $12.00 cap.
3. Metering is reported to date, not a settled invoice.
4. All final app and container states are saved separately from the billing snapshot.
5. The separate Pythonic sensitivity adds $0.7346, including failed/interrupted apps, for latest reported project cost $3.3456 against the additional $3.00 and total $12.00 caps.

After:

1. The pilot-based cost forecast for the primary campaign was $4.74--$8.14.
2. Before the follow-up, reported gross project spending was $2.6110, including setup and interrupted attempts, against the $12.00 cap.
3. These are reported charges, not a settled invoice.
4. Final app and container shutdown records are stored separately from the billing snapshot.
5. The separate Pythonic sensitivity added $0.7346, including failed and interrupted apps, bringing reported project spending to $3.3456, within the additional $3.00 and total $12.00 caps.

### Failure exclusions

Before:

1. Failures concentrate in particular decoder/task cells; exclusion cannot be assumed independent of treatment or difficulty.
2. The analysis frozen before execution counts them as incorrect.
3. We additionally exclude failures within each cell, exclude a model/item/run from all precision--decoder cells whenever any cell failed, and exclude whole items with any failure across conditions/runs.
4. The middle rule preserves a common observed cohort; its required-call whole-strict recovery is Qwen3-0.6B 2.1 [-0.7, 5.2]; Llama-3.2-1B -4.8 [-9.4, -0.5]; Llama-3.2-3B -2.1 [-5.1, 0.6] percentage points [95% CI].
5. Directional interval classifications change in 0 recovery effects and 0 decoder contrasts across all three rules and both endpoints.
6. Cell-only exclusion compares different completed populations; every exclusion selects on a post-treatment outcome and can favor easier items.
7. None identifies performance with unlimited generation or a repaired engine.
8. The released failure report includes every cell count, retained denominator and supplementary interval; primary results remain unchanged.

After:

1. Failures cluster by decoder and task; exclusion may depend on treatment or difficulty.
2. The analysis frozen before execution counts failures as incorrect.
3. Three sensitivity checks exclude failures per cell, remove a model--item--run from all precision--decoder cells if any cell failed, or remove whole items with any failure.
4. The second rule preserves a common observed cohort; its required-call whole-strict recovery is Qwen3-0.6B 2.1 [-0.7, 5.2]; Llama-3.2-1B -4.8 [-9.4, -0.5]; Llama-3.2-3B -2.1 [-5.1, 0.6] percentage points [95% CI].
5. Across all three rules and both endpoints, directional interval classifications change for 0 recovery effects and 0 decoder contrasts.
6. Cell-only exclusion changes the completed population; all three select on a post-treatment outcome and may favor easier items.
7. None estimates performance with unlimited generation or a repaired engine.
8. The failure report gives every cell count, retained denominator and supplementary interval; primary results remain unchanged.

### Settings appendix

Before:

1. Qwen uses enable_thinking=False.
2. These intervals describe item/schedule variation under that execution.
3. Exact executed worker sources and hash records are in provenance/; the maintained implementation is separate.
4. Historical launcher revisions were not retained, so we do not claim to have recovered them.

After:

1. Qwen runs in non-thinking mode (enable_thinking=False).
2. These intervals describe variation across items and schedules under that execution.
3. provenance/ holds exact executed worker sources and hashes, separately from maintained code.
4. Historical launcher revisions were not retained; no recovery is claimed.

## Verification

- Rebuilt PDF: six pages, checked with both the TeX build record and `pdfinfo`.
- Inspected the first and last pages rendered in grayscale; affiliation, email and final references are visible without clipping.
- No overfull boxes, undefined references or undefined citations in the final TeX log.
- All 36 existing tests pass.
- Saved inputs, primary and sensitivity results, figure files, executed worker snapshots and the pre-existing audits match their pre-edit SHA-256 hashes. Only the paper build record changed under `results/`.
- Numerical tables, the sensitivity token-limit table, setup, conclusion, replication table, references and method overview source are byte-for-byte unchanged.
- Body type sizes, margins and float spacing are unchanged. Prose was shortened to preserve six pages.
- Text generators were updated alongside generated TeX; no statistical calculation was changed. No cloud compute was run.

Total: 83 prior sentences replaced or removed; 88 revised or added sentences listed.
