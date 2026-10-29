# Audit of editing changes and Figure 1

Date: 2026-10-29. Scope: the 88 revised/added sentences listed in `paper/EDITING_CHANGES.md`, its author/verification statements, and Figure 1. This is a fresh read-only comparison with the 83 listed prior sentences, saved results and configuration. Unchanged paper material and the earlier release audit are not reopened.

**Outcome:** no numerical mismatch found in the listed revisions or Figure 1. One Medium and two Low wording findings remain. The sensitivity is explicitly separate from the primary matrix; neither the figure nor the revised text pools the 4,800 sensitivity responses into the 24,000 primary observations. No paper, source, figure or result file was edited.

## Findings, ranked by severity

### Medium — M1. The new Llama ordering needs a primary-contract and point-estimate qualification

Locations: [abstract](paper/generated/abstract_results.tex:1), sentence A3; [first introduction paragraph](paper/generated/intro_finding.tex:1), sentence I3.

> Whole-response constraints help F16 at least as much as Q4 for Llama, with nominally negative recovery for Llama-1B.

The primary required-call point estimates support this ordering, but the new sentence states it categorically. Llama-1B benefits by 43.1 points at F16 versus 38.4 at Q4, with incremental recovery −4.7 [−9.1, −0.3] points. Llama-3B benefits by 33.9 versus 31.8 points, but its interaction is −2.1 [−5.0, 0.6]: the interval permits either ordering. “Nominally negative” appropriately qualifies 1B; it does not qualify the preceding claim about both models.

The contract also matters: on the separate Pythonic parallel subset, Llama-1B's recovery is **+1.7 [−10.3, 13.7]** points, so even the point-estimate ordering is not universal across this paper's conditions. The introduction's preceding “primary comparison” helps, but the abstract should also name that scope. The old opening described observed format contrasts and did not assert this general precision ordering.

Recommended correction, not applied: specify **“On the primary JSON-contract point estimates …”**, and retain that only Llama-1B has a nominally negative primary required-call recovery interval. Do not turn Llama-3B's interval crossing zero into evidence that F16 benefits at least as much in the population. Evidence: [primary summary](results/full/full-002/summary.json), `recovery_effects`, required/whole_strict; [separate summary](results/sensitivity/pythonic-002/summary.json), parallel recovery.

### Low — L1. “Format … raises” is more causal than the prior descriptive wording

Locations: A4 in the abstract and I4 in the first introduction paragraph.

The old text said accuracy **“rises from”** and described a larger **observed contrast**. The new subjects/verbs are **“Meta's Pythonic format and matching grammar raise …”** and **“Meta's Pythonic format … raises …”**. All percentages are correct, and the nearby joint-intervention/nonrandomization caveats substantially limit the risk. Nevertheless, these verbs put the format itself in the causal role more directly than the old wording. The saved comparison changes prompt, parser and grammar, with different sessions/hosts and no randomized crossover.

Recommended correction, not applied: describe accuracy **observed under the Pythonic contract versus the primary JSON contract**, or a difference observed after the joint contract change. Preserve the separate-sensitivity label and the caveat; do not attribute the gain solely to Meta syntax or a parser. This is a wording concern, not an allegation of pooled results or an incorrect effect size. Evidence: [sensitivity manifest](data/pythonic/manifest.json), `prompt_scope`; [saved sensitivity report](results/sensitivity/pythonic-002/REPORT.md).

### Low — L2. Throughput wording changes lack of evidence into a categorical claim

Location: [execution paragraph](paper/main.tex:60), sentence E9.

Old: “The researcher permitted concurrent full studies after the separate pilots; **this does not establish isolated cross-model throughput**.”

New: “The researcher permitted concurrent full studies after separate pilots; **cross-model throughput was not isolated**.”

The saved authorization establishes permission for concurrent studies, and the recorded measurements include serving/slot contention. Neither alone measures the interference from another study or establishes the absence of every relevant form of isolation. The old sentence deliberately withheld an isolation claim; the rewrite asserts non-isolation. This is stronger literal wording even though it is conservative about performance interpretation and does not affect the accuracy results.

Recommended correction, not applied: retain **“these runs do not establish isolated cross-model throughput.”** Evidence: [concurrency authorization](results/ops/full-002_protocol_concurrent_studies.json), execution section; [integrity record](results/full/full-002/integrity.json), `latency_scope`.

## What was checked

- Every listed before sentence was located in the prior tracked TeX; every listed after sentence was located in the current TeX. Coverage is 83 prior and 88 revised/added sentences in 17 groups. Individual verdicts follow below.
- Recounted the 24,000 unique primary and 4,800 unique sensitivity scored observations, cell accuracies, primary structure-validity rates and completion statuses. Checked displayed CIs against the saved summary fields.
- Independently reproduced **20 matched-parallel sensitivity interval pairs**: eight accuracy intervals, eight Pythonic-minus-JSON contrast intervals, two recovery intervals and two changes in recovery. Regenerated 10,000 crossed item/run bootstrap draws using the recorded seed 20261028 and draw order, without calling the manuscript wording generator. Primary and exclusion intervals were checked against saved result fields, not re-estimated in this audit.
- Checked the interrupted sensitivity's 1,610 and continued 790 generation keys: disjoint, complete, and all saved failures retained. Confirmed their saved device labels, without normalizing A10G away.
- Checked the figure's source and its actual grayscale rendering on PDF page 2. Confirmed the PDF remains six pages. Existing tests pass: **36**. Provenance verification passes: **56 files across 6 archived submissions**. No cloud work or live billing query was performed.

## Numerical evidence

### N1. Matched parallel format sensitivity

All rows use the original 60 parallel items × five operational runs = 300 observations per cell. These are not the 120-item sensitivity aggregates.

| Quantity | Llama-1B | Llama-3B |
| --- | ---: | ---: |
| Primary JSON Q4 whole-strict correct / total | 3/300 = 1.0% | 0/300 = 0.0% |
| Pythonic Q4 whole-strict correct / total | 187/300 = 62.3% | 265/300 = 88.3% |
| Pythonic Q4 whole-strict accuracy CI, % | [50.0, 74.3] | [80.0, 95.7] |
| Pythonic-minus-JSON Q4 gain, pp [95% CI] | 61.3 [48.7, 73.3] | 88.3 [80.0, 95.7] |
| Pythonic F16-minus-Q4 whole-strict gap, pp | 6.0 | 3.3 |
| Pythonic incremental recovery, pp [95% CI] | 1.7 [−10.3, 13.7] | −3.3 [−8.7, 0.7] |
| Change in recovery versus JSON, pp [95% CI] | 2.3 [−10.0, 15.0] | −3.3 [−8.7, 0.7] |

These reproduce the saved [sensitivity summary](results/sensitivity/pythonic-002/summary.json) and [report](results/sensitivity/pythonic-002/REPORT.md). The two sensitivity recovery intervals and their two change intervals include zero. The format contrasts are large and positive; this does not establish quantization-specific recovery.

### N2. Changed primary result sentences

| Model | Q4 required-call free → whole strict, % | Q4 whole-strict all-case accuracy, % [95% CI] | Q4 whole-strict structure validity, % [95% CI] |
| --- | --- | --- | --- |
| Qwen3-0.6B | 70.7 → 75.6 | 73.0 [66.9, 79.0] | 100.0 [100.0, 100.0] |
| Llama-3.2-1B | 14.2 → 52.7 | 47.4 [40.5, 54.2] | 100.0 [100.0, 100.0] |
| Llama-3.2-3B | 29.2 → 61.0 | 54.9 [48.0, 61.7] | 100.0 [100.0, 100.0] |

All match [primary summary](results/full/full-002/summary.json) and [primary report](results/full/full-002/REPORT.md). Required-call accuracy uses 180 items; all-case accuracy and structure validity use 200. Removing the repeated model name from the structure-validity sentence does not alter its model: the preceding sentence supplies it.

### N3. Primary generation status sentence

The saved scored rows contain 23,860 `ok`, 139 `token_limit` and one `grammar_trigger_replay_error`, summing to 24,000. The [failure sensitivity](results/full/full-002/failure_sensitivity.json), `token_limit_runtime`, confirms all 139 limits have tokens_predicted=512, stop_type=limit and cap=512. Thus “completed normally” denotes the operational status, not correctness; “one failed during grammar replay” and the 512-token limit are accurate.

### N4. Separate sensitivity continuation

The three submitted saved generation streams contain 2,400, 1,610 and 790 responses. The last two cover the 3B matrix without overlap. Their token-limit counts are 13 and 6, all retained. Device-reported names are NVIDIA A10G for the interrupted submission and NVIDIA A10 for the continuation; the latter supports the new “Another A10” sentence. Sources: [sensitivity state](results/sensitivity/pythonic-002/state.json), [continuation completion](results/sensitivity/pythonic-002/pythonic-002-3_completion.json), and the three `pythonic-002-*.jsonl` streams.

### N5. Post-hoc failure exclusions

The “second rule” is the same `matched_panel` rule previously called “middle.” Its required-call whole-strict recoveries are Qwen 2.1 [−0.7, 5.2], Llama-1B −4.8 [−9.4, −0.5], and Llama-3B −2.1 [−5.1, 0.6] pp. There are zero changed interval classifications among 54 recovery effects and 36 decoder contrasts across all three rules and both endpoints. These match [FAILURE_SENSITIVITY.md](results/full/full-002/FAILURE_SENSITIVITY.md) and [failure_sensitivity.json](results/full/full-002/failure_sensitivity.json). Every exclusion remains described as post-treatment selection, without an unlimited-generation claim.

## Figure 1: setup and count reconciliation

Source: [method_overview.tex](paper/method_overview.tex). No count or scope mismatch found.

| Figure element | Saved setup/result check | Verdict |
| --- | --- | --- |
| Three models | Qwen3-0.6B, Llama-3.2-1B-Instruct and Llama-3.2-3B-Instruct in `configs/full_models.json`; short labels identify the same models | Pass |
| Two precisions | F16 and Q4_K_M in primary protocol and all primary cells | Pass |
| Four primary arms | free, loose, trigger_strict, whole_strict | Pass |
| 200 primary items | 60 simple + 60 multiple + 60 parallel + 20 irrelevance | Pass |
| Five operational runs | Labels 101, 211, 307, 401, 503, retained as operational repeats | Pass |
| 24,000 outputs | 3 × 2 × 4 × 200 × 5, matching the complete primary matrix | Pass |
| 180 required / 20 irrelevance | Primary endpoint excludes irrelevance; the separate helper is explicitly shown | Pass |
| Official checker → recovery | Declared call adapters feed official AST matching; R_d=L_f−L_d matches the paper's definition | Pass |
| Two-model sensitivity | Both Llama models only, two precisions, free/whole strict only | Pass |
| 120 sensitivity items | Original 60 parallel + separately sampled 60 parallel_multiple | Pass |
| 4,800 sensitivity outputs | 2 × 2 × 2 × 120 × 5; distinct from the 24,000 primary outputs | Pass |
| Matched JSON contrast: 60 parallel | Only those original items have a matched primary JSON counterpart | Pass |
| Separate dashed branch / “not pooled” | Dashed box and connector remain visually distinct, labeled with its own AST scores/recovery; no merge into primary recovery | Pass |

The figure renders clearly in grayscale, with readable labels and arrows and no clipping in the inspected PDF. The drawing floats above the Experimental design heading on page 2; that placement does not change its counts or imply pooled analysis.

## Sentence-by-sentence ledger

Each row corresponds to an **After** entry in `EDITING_CHANGES.md`; no revised sentence is omitted. “Pass” confirms numerical consistency where applicable and no stronger substantive claim than the old wording in its paragraph context. Findings M1/L1/L2 are exceptions requiring qualification or preservation of the old epistemic wording. Model names, Q4/F16 identifiers and the A10 selector are identifiers/settings, not additional measured quantities.

Evidence keys: **P** = [primary summary](results/full/full-002/summary.json), [scored rows](results/full/full-002/scored.jsonl), [integrity](results/full/full-002/integrity.json) and [report](results/full/full-002/REPORT.md); **S** = [sensitivity summary](results/sensitivity/pythonic-002/summary.json), scored/raw streams and report; **F** = [failure sensitivity](results/full/full-002/failure_sensitivity.json) and report; **C** = [primary costs](results/full/full-002/costs.json), sensitivity summary costs and saved billing snapshots; **D** = [primary protocol](configs/protocol.json), [primary manifest](data/manifest.json), [sensitivity manifest](data/pythonic/manifest.json), frozen request bundles and preparation sources; **G** = compiler, saved membership records and [offline validation](results/offline/grammar_validation.json); **W** = [executed-source manifest](provenance/executed-workers/manifest.json), hash records and primary session metadata; **Q** = official checker adapter in `qunti/scoring.py`, executed snapshots and the pinned checker. N1–N5 refer to the numerical reconciliations above.


### Abstract

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **A1**. Does strict grammar decoding recover what Q4 quantization loses in small-model tool calling? | N/A; Q4 is the saved weight format. | **Pass** — Research question, not a claim that a positive free-decoding loss was established. |
| **A2**. We find no clear quantization-specific recovery. | No positive primary whole-strict recovery interval excludes zero [P]. | **Pass** — Read as no clear positive recovery, not evidence of equivalence; the following nominal-negative qualification remains. |
| **A3**. Whole-response constraints help F16 at least as much as Q4 for Llama, with nominally negative recovery for Llama-1B. | F16/Q4 and model labels match [P]; see M1 for the actual interaction intervals. | **M1** — Missing primary-contract and point-estimate qualifications; Llama-3B does not establish the asserted ordering. |
| **A4**. In a separate sensitivity, Meta's Pythonic format and matching grammar raise Q4 whole-strict parallel accuracy from 1.0% to 62.3% for Llama-1B and 0.0% to 88.3% for Llama-3B on the same 60 cases. | 1.0→62.3 and 0.0→88.3%; 60 matched parallel items [N1]. | **L1** — The explicit separate-sensitivity scope is preserved, but the transitive verb “raise” is stronger causal shorthand than “rises.” |
| **A5**. Paired gains of 61.3 [48.7, 73.3] and 88.3 [80.0, 95.7] points far exceed Pythonic F16-to-Q4 gaps of 6.0 and 3.3 points. | 61.3 [48.7,73.3], 88.3 [80.0,95.7] pp; gaps 6.0 and 3.3 pp [N1]. | **Pass** — Same numerical comparison as before. Gaps are observed Pythonic whole-strict gaps, not an interval-tested universal ordering. |
| **A6**. A format contract means the prompt, parser and grammar. | N/A. | **Pass** — Explicit definition of the existing joint prompt/parser/grammar intervention, not a new result. |
| **A7**. This nonrandomized sensitivity changes all three, separately from the primary BFCL conceptual replication; it does not isolate a parser-only causal effect. | N/A [S, D]. | **Pass** — Retains nonrandomization, the joint intervention, separation from the primary replication, and no parser-only attribution. |
| **A8**. Quantization-specific recovery and its change from JSON remain inconclusive in the sensitivity. | Parallel Pythonic recovery and change-from-JSON intervals all include zero [N1]. | **Pass** — Same inconclusive-interaction claim, scoped to the sensitivity rather than primary Llama-1B. |

### Introduction, first paragraph

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **I1**. Does strict grammar decoding recover tool-calling accuracy lost to Q4 quantization? | N/A; Q4 matches [D]. | **Pass** — Question only; no asserted precision loss. |
| **I2**. The primary comparison shows no clear quantization-specific recovery. | Primary whole-strict intervals: Qwen 2.1 [-0.7,5.2], Llama-1B -4.7 [-9.1,-0.3], Llama-3B -2.1 [-5.0,0.6] pp [P]. | **Pass** — No clear positive quantization-specific recovery; not a claim that all interactions equal zero. |
| **I3**. Whole-response constraints help F16 at least as much as Q4 for Llama, with nominally negative recovery for Llama-1B. | Same interaction evidence as A3 [P]. | **M1** — Same ordering and scope problem as A3. |
| **I4**. Yet Meta's Pythonic format in a separate sensitivity raises Q4 whole-strict accuracy from 1.0% to 62.3% for Llama-1B and 0.0% to 88.3% for Llama-3B on the same 60 parallel cases, far exceeding Pythonic precision gaps of 6.0 and 3.3 points. | 1.0→62.3 and 0.0→88.3%; same 60 parallel cases; Pythonic whole-strict gaps 6.0/3.3 pp [N1]. | **L1** — Separate and matched-item scope remains explicit; “format … raises” adds causal shorthand. |
| **I5**. This changes prompt, parser and grammar together; it establishes neither a general rule about quantization nor an intrinsic Llama limitation. | N/A [S, D]. | **Pass** — Retains the joint intervention and the previous restriction against general or intrinsic-model conclusions. |

### Introduction, motivation

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **IM1**. Prior work separates structural and content failures and tests grammar mitigation in quantized models. | N/A. | **Pass** — “Tests” replaces “studies”; it does not add a new prior-work attribution. |
| **IM2**. We ask whether strict enforcement changes the incremental precision gap differently from permissive or trigger-gated grammars. | N/A [D]. | **Pass** — Same strict-versus-permissive/trigger-gated interaction question. |
| **IM3**. A quantized model can gain simply because an intervention helps every precision. | N/A. | **Pass** — Same explanation of why matched F16 controls are needed. |
| **IM4**. A grammar admitting arbitrary text cannot guarantee schema-valid output. | N/A [G]. | **Pass** — Same absence of a validity guarantee for an arbitrary-text escape; not a claim that every loose output fails. |
| **IM5**. We therefore use matched full-precision controls and check what each decoder admits. | N/A [D, G]. | **Pass** — Same matched controls and admitted-language validation, stated directly. |

### Frozen tasks and prompts

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **F1**. All conditions share original items and accepted answers, selected without model predictions. | Shared frozen item IDs and accepted answers verified [D]. | **Pass** — Same condition matching and no outcome-based selection. |
| **F2**. Prompts are frozen from pinned publisher templates with a fixed Llama template date. | N/A; fixed template-date field and pinned revisions retained [D]. | **Pass** — Only punctuation changes; no stronger template claim. |

### Precision and hardware records

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **PH1**. The checkpoint's storage dtype may differ from the F16 reference. | F16 is the exported reference [D, W]. | **Pass** — Weaker possibility statement; preceding unchanged sentence still identifies the F16 export. |
| **PH2**. Model revisions, source and output hashes, conversion commands, server arguments and the pinned llama.cpp source [llamacpp] are recorded. | Source/output and engine identifiers remain recorded [P, W]. | **Pass** — Spells out the slash; no new provenance claim. |
| **PH3**. Each model uses one A10 worker for all arms and precisions, with a fixed Modal allocation selector. | One A10-selected worker per complete primary model session; all 8,000 observations per model retained [P, W]. | **Pass** — Combines the old worker and selector statements; it does not describe the restarted separate sensitivity. |
| **PH4**. Records retain device-reported A10/A10G labels and drivers; model sessions may use different physical hosts. | Recorded device labels include A10/A10G [P, S]. | **Pass** — Same retained-label and potentially different-host qualification. |

### Decoder prompt contract

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **DC1**. Each model's arms share rendered prompts and offered tools. | Shared prompt bundles and offered tools [D, P]. | **Pass** — Same within-model matching, not a claim of identical prompts across models or protocols. |
| **DC2**. Both revisions share the template hash in Appendix [app:settings]. | Two selected Llama revisions share the recorded template hash [D]. | **Pass** — Same claim; the hash-convention issue in the unchanged appendix is outside this audit. |
| **DC3**. We added a system-message JSON-array convention for parallel calls, but the HF template's later user-message instruction requests one JSON object. | One-object instruction and study-added array convention are both in frozen Llama prompts [D]. | **Pass** — Retains instruction order, JSON-array convention, and the conflicting single-object instruction. |
| **DC4**. Meta documents Pythonic call lists [metaprompt], which the primary JSON contract does not evaluate. | N/A; [metaprompt] citation key is unchanged. | **Pass** — Same documented call-list claim and primary-JSON exclusion; no new citation or format claim. |
| **DC5**. Llama findings concern this declared contract, not its best supported interface. | N/A. | **Pass** — Same scope limitation inside the primary-JSON-contract paragraph; does not remove the separate sensitivity. |

### Schema compilation

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **SC1**. The compiler allows documented object keys in any order, requires specified keys and forbids duplicates. | N/A [G, W]. | **Pass** — Required keys, uniqueness and arbitrary ordering of documented keys were already claimed. |
| **SC2**. As an explicit API policy, known property sets are closed; free-form dictionaries stay free-form. | N/A [G, W]. | **Pass** — Joins two old sentences; closed documented schemas and free-form dictionaries remain distinguished. |
| **SC3**. For nested BFCL dictionaries with untyped required fields, names are retained but values are unconstrained; answers never supply types. | N/A [G, W]. | **Pass** — Same untyped-required-field normalization and prohibition on using accepted answers for types. |
| **SC4**. These normalization choices are released as part of the intervention. | N/A [G, W]. | **Pass** — Same released intervention/normalization scope. |

### Grammar validation

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **GV1**. Finite character-level membership checks test selected schemas, malformed strings, unknown functions, missing or extra arguments, types, key order, parallel calls and abstention. | N/A; selected-schema membership cases are saved [G]. | **Pass** — Same finite coverage list; “missing or extra” spells out the slash. |
| **GV2**. These show tested coverage, without proving every JSON Schema feature or token-level behavior. | N/A [G]. | **Pass** — Preserves the distinction between tested coverage and a general schema/token-runtime proof. |
| **GV3**. Before collection, synthetic runtime probes force a known trigger to verify literal replay and the server's configured lazy mode. | N/A; saved primary runtime-probe events confirm the stated checks [P]. | **Pass** — Same before-collection trigger/literal-replay/lazy-mode checks. |
| **GV4**. These are setup checks, not benchmark successes. | N/A [G, P]. | **Pass** — Same separation of setup probes from benchmark successes. |

### Execution

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **E1**. Decoding uses temperature zero and shuffled requests, with seed and schedule labels frozen before execution. | Temperature 0.0; frozen run seeds/schedules and shuffled requests [D, P, W]. | **Pass** — Same settings and request order policy. |
| **E2**. Identical greedy outputs remain operational repeats, not independent items. | N/A. | **Pass** — Same clustering warning; identical greedy repeats are not new items. |
| **E3**. Context and output limits, slots, cache settings and stop strings match across arms. | Context/output/slots/cache/stop controls match in saved integrity records [P]. | **Pass** — Same per-arm controls; no new equality claim. |
| **E4**. Llama uses publisher token IDs to avoid duplicating the template's beginning-of-text marker. | N/A; saved Llama workers tokenize with publisher IDs [W]. | **Pass** — Same avoidance of duplicate template BOS. |
| **E5**. An earlier collection with that duplication remains an aborted setup attempt, stopped before accuracy inspection. | N/A; aborted attempt appears in primary state/cost records [P, C]. | **Pass** — Same retained setup attempt and before-accuracy-inspection limitation. |
| **E6**. Qwen prompts remain strings, using publisher settings that disable an added beginning-of-text token. | N/A; Qwen string prompt path and add-BOS setting [W, P]. | **Pass** — Expands BOS into plain language without changing the prompt transport claim. |
| **E7**. Logs retain cache-reuse timings and actual generation settings. | N/A [P, W]. | **Pass** — Same logged cache timings and actual generation settings. |
| **E8**. The cloud supervisor checkpoints events and enforces queue, runtime and scheduling limits frozen before execution. | N/A [D, W]. | **Pass** — Same checkpoint/bounds/scheduling enforcement; does not claim isolated throughput. |
| **E9**. The researcher permitted concurrent full studies after separate pilots; cross-model throughput was not isolated. | N/A; saved concurrency authorization [D]. | **L2** — Permission to overlap is established; “was not isolated” is a stronger categorical statement than the old absence-of-evidence wording. |

### Scoring

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **S1**. Official BFCL AST matching determines correctness [bfcl]. | N/A [Q]. | **Pass** — Same official AST correctness authority. |
| **S2**. We parse the declared JSON envelope into calls without executing them. | N/A [Q]. | **Pass** — Same envelope-to-call adapter and nonexecution of generated calls. |
| **S3**. The unchanged official irrelevance helper uses the same parsing adapter. | N/A [Q]. | **Pass** — Same unchanged official irrelevance helper and parsing adapter. |
| **S4**. Irrelevance can credit outputs with no parsed call even when our format diagnostic rejects their prose; we report these separately. | N/A [Q, P]. | **Pass** — Same possibility of irrelevance credit despite rejected prose, and separate reporting. |

### Paired uncertainty

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **U1**. Item-only intervals provide a sensitivity check. | N/A; item-only CI fields are saved [P]. | **Pass** — Same supplementary sensitivity check. |
| **U2**. Intervals are pointwise and unadjusted for multiple comparisons; exploratory contrasts are labeled. | N/A; paired percentile intervals are explicitly pointwise/unadjusted [P, S]. | **Pass** — Same multiplicity and exploratory labeling qualification. |
| **U3**. Without observed failures, empirical bootstrap intervals can degenerate and cannot bound rare unobserved population failures. | N/A. | **Pass** — Same empirical-bootstrap boundary caveat; does not claim a population failure bound. |
| **U4**. The recovery share $R_d/L_f$ is undefined for nonpositive observed free loss. | N/A; ratio policy and undefined fields agree with [P]. | **Pass** — Same reporting convention for nonpositive observed free loss; not a new algebraic claim. |
| **U5**. We withhold its interval when bootstrap denominators are unstable and never clip values into a partition. | N/A; unstable denominators remain flagged [P]. | **Pass** — Same interval-withholding and no-clipping rule. |

### Practical follow-up

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **PF1**. The planned follow-up compares schema-audit and precision-fallback methods with ordinary retries; these methods are not evaluated here. | The removed “Direction 2” is an internal plan label, not a numerical result. | **Pass** — Same unevaluated schema-audit/precision-fallback follow-up and ordinary-retry comparator. |

### Results prose

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **R1**. For Qwen3-0.6B, Q4 required-call accuracy rises from 70.7% with free decoding to 75.6% with whole-response constraints. | Qwen Q4 required accuracy 70.7→75.6% [N2]. | **Pass** — Same point comparison; “rises” describes the saved within-primary-arm contrast. |
| **R2**. Across all cases, Q4 whole-strict response-structure validity is 100.0 [100.0, 100.0]%, while official accuracy is 73.0 [66.9, 79.0]%. | 100.0 [100.0,100.0]% validity; 73.0 [66.9,79.0]% all-case accuracy [N2]. | **Pass** — Model identity remains supplied by the preceding Qwen sentence; no validity-to-correctness inference added. |
| **R3**. For Llama-3.2-1B, Q4 required-call accuracy rises from 14.2% with free decoding to 52.7% with whole-response constraints. | Llama-1B Q4 required accuracy 14.2→52.7% [N2]. | **Pass** — Same point comparison. |
| **R4**. Across all cases, Q4 whole-strict response-structure validity is 100.0 [100.0, 100.0]%, while official accuracy is 47.4 [40.5, 54.2]%. | 100.0 [100.0,100.0]% validity; 47.4 [40.5,54.2]% all-case accuracy [N2]. | **Pass** — Preceding Llama-1B sentence supplies the model; numbers and scope unchanged. |
| **R5**. For Llama-3.2-3B, Q4 required-call accuracy rises from 29.2% with free decoding to 61.0% with whole-response constraints. | Llama-3B Q4 required accuracy 29.2→61.0% [N2]. | **Pass** — Same point comparison. |
| **R6**. Across all cases, Q4 whole-strict response-structure validity is 100.0 [100.0, 100.0]%, while official accuracy is 54.9 [48.0, 61.7]%. | 100.0 [100.0,100.0]% validity; 54.9 [48.0,61.7]% all-case accuracy [N2]. | **Pass** — Preceding Llama-3B sentence supplies the model; numbers and scope unchanged. |
| **R7**. 23,860 generations completed normally, 139 reached the 512-token cap, and one failed during grammar replay. | 23,860 ok + 139 token-limit + 1 grammar replay = 24,000; all limits at 512 tokens [N3]. | **Pass** — Exact plain-language replacement for raw keys; 512 is also independently present in execution metadata. |

### Separate format sensitivity

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **PS1**. We collected 4,800 responses on 120 cases: the original parallel and a separately sampled parallel-multiple subset. | 4,800 responses / 120 cases; original 60 parallel + separately sampled 60 parallel-multiple [D, S]. | **Pass** — Same collection; still labeled a separate sensitivity. |
| **PS2**. Both Llama models used both precisions, free and whole-strict decoding, and the same operational labels. | 2 Llama models × 2 precisions × 2 arms × 120 items × 5 labels [D, S]. | **Pass** — Splits the old long sentence; same design. |
| **PS3**. The prompt uses Meta's call-list syntax, omits the HF tools instruction and uses [] for abstention. | N/A; [] convention and omitted HF tools injection match frozen Pythonic prompts [D]. | **Pass** — Same prompt convention; “Meta’s” modifies call-list syntax, not the study-specific abstention sentinel. |
| **PS4**. Its Pythonic parallel incremental recovery is 1.7 [-10.3, 13.7] points; the paired change in recovery versus JSON is 2.3 [-10.0, 15.0] points. | 1.7 [-10.3,13.7] pp recovery; 2.3 [-10.0,15.0] pp change [N1]. | **Pass** — Only sentence splitting; intervals remain inconclusive. |
| **PS5**. Llama-3.2-3B Q4 whole-strict parallel accuracy is 88.3 [80.0, 95.7]%, versus 0.0% under the original JSON contract. | 3B 88.3 [80.0,95.7]% vs 0.0% under primary JSON [N1]. | **Pass** — Only sentence splitting; still the matched parallel endpoint, not the 120-case aggregate. |
| **PS6**. Only the original parallel items are matched across the changed prompt, parser and grammar. | Only 60 original parallel items are matched across protocols [D]. | **Pass** — Same restriction; parallel-multiple is not given a nonexistent JSON baseline. |
| **PS7**. A platform interruption left 1,610 saved Llama-3B outputs. | 1,610 generation records in the interrupted 3B submission [N4]. | **Pass** — Same interruption/count claim, with “durable” expressed as saved outputs. |
| **PS8**. Another A10 collected the remaining 790 responses, retaining all saved failures. | 790 disjoint continuation records on A10; 1,610+790=2,400 for 3B [N4]. | **Pass** — Same continuation and retention of saved failures; no pooling of duplicate cells. |

### Costs

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **C1**. The pilot-based cost forecast for the primary campaign was $4.74--$8.14. | $4.74–$8.14 after rounding the pilot forecast [C]. | **Pass** — Same forecast, without representing it as measured spending. |
| **C2**. Before the follow-up, reported gross project spending was $2.6110, including setup and interrupted attempts, against the $12.00 cap. | $2.6110 reported gross pre-follow-up spending; $12.00 cap [C]. | **Pass** — Same historical snapshot and inclusion of setup/interrupted attempts. |
| **C3**. These are reported charges, not a settled invoice. | N/A; settled=false [C]. | **Pass** — Preserves the reported-versus-settled distinction. |
| **C4**. Final app and container shutdown records are stored separately from the billing snapshot. | N/A; shutdown app/container snapshots are separate saved artifacts. | **Pass** — Same storage claim for final states, now referring to shutdown records; not a live-status assertion. |
| **C5**. The separate Pythonic sensitivity added $0.7346, including failed and interrupted apps, bringing reported project spending to $3.3456, within the additional $3.00 and total $12.00 caps. | $0.7346 optional; $3.3456 project; $3.00 optional and $12.00 project caps [C]. | **Pass** — Same amounts and failed/interrupted-attempt inclusion; “within” is supported by the recorded values, not a settled-invoice claim. |

### Failure exclusions

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **X1**. Failures cluster by decoder and task; exclusion may depend on treatment or difficulty. | N/A; nonuniform failures visible in [F]. | **Pass** — Same warning that exclusion may depend on treatment or difficulty. |
| **X2**. The analysis frozen before execution counts failures as incorrect. | N/A; all 140 primary failures have correct=false [P, F]. | **Pass** — Same frozen failure-inclusive policy. |
| **X3**. Three sensitivity checks exclude failures per cell, remove a model--item--run from all precision--decoder cells if any cell failed, or remove whole items with any failure. | Exactly 3 rules in [F]: cell_completed, matched_panel, complete_item. | **Pass** — Same masks; “model--item--run” replaces slash notation, and whole-item exclusion still ranges over conditions/runs. |
| **X4**. The second rule preserves a common observed cohort; its required-call whole-strict recovery is Qwen3-0.6B 2.1 [-0.7, 5.2]; Llama-3.2-1B -4.8 [-9.4, -0.5]; Llama-3.2-3B -2.1 [-5.1, 0.6] percentage points [95% CI]. | Matched required whole-strict: Qwen 2.1 [-0.7,5.2], 1B -4.8 [-9.4,-0.5], 3B -2.1 [-5.1,0.6] pp, 95% CIs [N5]. | **Pass** — “Second” replaces “middle”; same matched cohort and interval values. |
| **X5**. Across all three rules and both endpoints, directional interval classifications change for 0 recovery effects and 0 decoder contrasts. | 0 changed classifications in 54 recovery effects and 36 decoder contrasts, across 3 rules and 2 endpoints [F]. | **Pass** — Same zero-change result; no claim of identical point estimates. |
| **X6**. Cell-only exclusion changes the completed population; all three select on a post-treatment outcome and may favor easier items. | N/A [F]. | **Pass** — Same population-selection and post-treatment bias warning. |
| **X7**. None estimates performance with unlimited generation or a repaired engine. | N/A [F]. | **Pass** — Same refusal to infer unlimited-generation or repaired-engine performance. |
| **X8**. The failure report gives every cell count, retained denominator and supplementary interval; primary results remain unchanged. | N/A [F]. | **Pass** — Same saved diagnostics and unchanged-primary-results claim. |

### Settings appendix

| ID / revised sentence | Number check | Wording verdict |
| --- | --- | --- |
| **AP1**. Qwen runs in non-thinking mode (enable_thinking=False). | enable_thinking=False matches frozen Qwen prompts [D]. | **Pass** — Same flag, with its meaning explained. |
| **AP2**. These intervals describe variation across items and schedules under that execution. | N/A; item/run resampling units match [P]. | **Pass** — Same restricted uncertainty scope. |
| **AP3**. provenance/ holds exact executed worker sources and hashes, separately from maintained code. | 56 executed source files across 6 submissions match recorded hashes [W]. | **Pass** — Same exact-source/archive-versus-maintained-code distinction. |
| **AP4**. Historical launcher revisions were not retained; no recovery is claimed. | N/A [W]. | **Pass** — Same lack of recovered historical launchers; “recovery” here concerns source provenance, not the accuracy estimand. |

## Author block and editing-log verification statements

- The affiliation and email match the supplied author instructions and the rendered author block. They are metadata, not results-derived assertions; no independent institutional/employment verification was attempted.
- The editing log’s six-page, 36-test, no-overfull/undefined-reference statements check against the current PDF/build record, fresh tests and final TeX log.
- The current tracked diff leaves saved inputs, numerical result artifacts, figure data, executed snapshots and earlier audits unchanged, except the expected paper-build record. Available pre-edit hashes also match those protected files. The numerical tables, setup and conclusion retain their pre-edit bytes. This is not a claim that PDF pagination or wording stayed identical.
- The main preamble’s type sizes, margins and float spacing are unchanged from the available pre-edit snapshot; the generated prose has corresponding generator changes. No statistical algorithm was changed by this editing pass.
- Only this audit file was added during the review. Recommendations above are unapplied.
