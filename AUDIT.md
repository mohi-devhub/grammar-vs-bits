# Pre-release audit

Audited 2026-10-29, treating the manuscript and implementation as untrusted artifacts. Only this file was added. No experiment, model inference, cloud job, dependency installation, or manuscript rebuild was run.

**Verdict:** I found no numerical mismatch in the checked paper tables, results prose, reports, or independently recomputed scores and intervals. I would resolve the high-severity findings before public release. The main scientific concern is the description of the Llama serving contract, rather than an arithmetic error. The other high-severity findings concern whether the code release contains the executed source and adequate licensing information.

Audited PDF: [paper/main.pdf](paper/main.pdf), six pages, SHA-256 `ebdc97a2459d6ee0fcbba5c5622e76c80cb90d65bd992edfac7786bef48b241b`.

## Findings, ranked by severity

### H1 — High: the Llama contract is described as native without adequately qualifying its format and parallel-call conflict

**Location:** PDF pp. 2 and 5, §§3.2 and 6; [prepare_full.py](scripts/prepare_full.py#L22), [scoring.py](qunti/scoring.py#L24), and the frozen Llama request bundles in [data/full_requests](data/full_requests).

The experiment requests a JSON object for one Llama call and a JSON array for several. The publisher HF template used by the experiment also inserts a later user-message instruction specifying a single JSON object. For example, the frozen `parallel_191` prompt contains both instructions. The paper repeatedly calls this a native contract without identifying that parallel JSON arrays are an added study convention.

Meta's separate official Llama-3.2 prompt documentation describes a Pythonic list of calls and explicitly supports multiple calls. This is a different documented contract, not evidence that Llama-3.2 inherently lacks parallel calling. See the [publisher prompt documentation](https://github.com/meta-llama/llama-models/blob/0e0b8c519242d5833d8c11bffc1232b77ad7f301/models/llama3_2/text_prompt_format.md). The experiment's HF template is publisher-provided too; the discrepancy must be explained rather than silently choosing one as the unique native protocol.

This matters because the paper's Q4 whole-strict parallel accuracies are only 1.0% for Llama-1B and 0.0% for Llama-3B. Raw free outputs also show format disagreement: `parallel_57` in the 3B F16/free/run-101 session emits semicolon-separated JSON call objects, which the study's JSON object/array parser rejects. That example establishes a representation failure, not that its argument values were otherwise correct.

**Reviewer consequence:** the measured gains and precision interactions are valid for the declared custom serving contract, but are not established measurements of best-practice native Llama tool calling. A common prompt across arms does not remove an interaction between a format mismatch and constrained decoding. Excluding token-limit/replay failures does not test this confound.

**Suggested resolution:** identify the exact HF-template variant, describe the JSON-array parallel convention and conflicting template instruction, and qualify the native-language claim and Llama interpretation. Establishing performance under the alternative publisher protocol would be a separate experiment, not something this audit establishes.

### H2 — High: the release omits the exact worker source used for the Qwen primary matrix

**Location:** PDF p. 2, execution/provenance claims; [full-002-1_worker_source.json](results/ops/full-002-1_worker_source.json), [pilot.py](scripts/pilot.py#L73), and [package_release.py](scripts/package_release.py#L11).

The Qwen primary batch records hashes for an older `full_runner.py`, `supervision.py`, and `common.py`. All three differ from the current released files. The older bytes remain locally under `.cache/pilot-snapshots/full-002-1/qunti/`, but `.cache` is excluded from the release. None of those three recorded hashes appears anywhere in the release file inventory. Both completed Llama sessions' recorded worker hashes match the current source.

For a concrete check, Qwen's recorded `full_runner.py` SHA-256 starts `432a9be7c3cb`; the released file starts `e24585212ee5`. The difference includes prompt-tokenization metadata and failure handling, not just formatting. This does **not** establish that Qwen accuracy changed: it establishes that the executed version cannot be reconstructed from the public artifact as packaged. The repository currently has no commits, so Git history cannot supply the missing version either.

**Suggested resolution:** ship the executed first-party source snapshots in a non-cache provenance directory, with the existing hashes, and identify the corresponding orchestration/runtime source versions. Preserve the current corrected implementation separately. Hashes alone are not a source-code release.

### H3 — High, release readiness: code/data licensing and redistribution notices are absent

**Location:** release file inventory and [package_release.py](scripts/package_release.py#L11).

There is no first-party `LICENSE` or equivalent file, and the release inventory contains no `LICENSE`/`NOTICE` files. The bundle redistributes selected BFCL inputs and reference answers. The pinned upstream Gorilla repository has an [Apache-2.0 license](https://raw.githubusercontent.com/ShishirPatil/gorilla/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/LICENSE), whose redistribution section specifies license-copy and attribution requirements. Data-specific terms must also be checked rather than assuming every artifact inherits the code license.

Even adding a root `LICENSE` would not include it in the current archive: the packager uses a fixed root allowlist that omits that filename.

**Suggested resolution:** choose and state the first-party code license, establish applicable terms for redistributed benchmark material, include the corresponding notices, and ensure the packager includes them. Model-license checks and exclusion of model weights do not resolve these separate omissions. This finding concerns missing release information; it is not a determination that a particular data redistribution is prohibited.

### M1 — Medium: the PDF promises a release but provides no way to locate this study's artifacts

**Location:** abstract and §§3–5; [paper/main.tex](paper/main.tex).

The abstract says raw outputs and code are released, and the methods repeatedly say settings and hashes are recorded. The PDF has no study repository URL, archive DOI, or availability statement. Its GitHub links identify other projects. The local archive exists, but a reader receiving only the paper cannot find the supplementary data or reproduction commands.

**Suggested resolution:** add a stable public artifact link and identify the experiment/release version before sharing the standalone paper. Publicly linkable protocol history would also support the repeated “registered” terminology; a frozen local protocol is not by itself evidence of public preregistration. Do not imply a registration venue that does not exist.

### M2 — Medium: relevant citations are missing, although the existing references checked out

**Location:** PDF p. 1, §2, and bibliography.

Two omissions are particularly relevant:

- Zhang, Chen, Li, and Wang, [Don't Fine-Tune, Decode: Syntax Error-Free Tool Use via Constrained Decoding, arXiv:2310.07075v3](https://arxiv.org/abs/2310.07075v3), is direct prior work on enforcing tool-call syntax. It is already listed in this repo's RELATED_WORK.md but absent from the manuscript bibliography.
- Tang and Zheng, [Measuring the Serving Stack Instead of the Model: Hidden Confounds in Local Tool-Use Evaluation, arXiv:2609.26693v1](https://arxiv.org/abs/2609.26693v1), directly examines model-dependent protocol effects, including Llama-3.2 and constrained-decoding non-termination. It bears on H1. It does not answer this paper's matched weight-precision interaction and should not be described as doing so.

The publisher model/prompt documents also need citations, especially when the paper calls a format native. The [Qwen3 model card](https://huggingface.co/Qwen/Qwen3-0.6B) documents its thinking/non-thinking distinction, which is relevant to the executed configuration.

I did not find a fabricated title, incorrect author list, or wrong linked paper among the existing thirteen entries. Missing literature is the issue here, not invented citations.

### M3 — Medium: the replication target and success criteria need a more explicit mapping

**Location:** title, abstract, and §2. Supporting audit material exists in [DIRECTIONS.md](docs/DIRECTIONS.md), but is not condensed into the paper.

The paper fairly says the interventions are mechanism-matched rather than bit-for-bit reproductions. Nevertheless, a reader is not shown which specific prior result is being reproduced, which parts are changed, or what counts as confirmation or contradiction. The source-faithful prompt/envelope probe proposed in DIRECTIONS.md is not demonstrated by the released synthetic trigger probes; those force a literal artificial call and test serving behavior.

The distinctions matter:

| Replicated work | Primary-source check | Consequence for this study |
| --- | --- | --- |
| QuantCall | Its [pinned corrected report](https://github.com/Happynood/quant-toolcall-bench/blob/6b6e29e5c83a91a52bdfc68b5f3063de172c0e55/docs/constrained_decoding_findings.md) compares one constrained seed with three free seeds and uses an arbitrary-text escape. The paper's description is correct. | The loose arm reproduces that mechanism, not its exact prompts, dataset mix, or reported metrics. Its null cannot be treated as a failed test of strict enforcement. |
| QuantMCP | Its [pinned run report](https://github.com/Happynood/quant-mcp-bench/blob/fc98a47c6a0ef77bb8be3a915016b42d203faf45/docs/RUN_REAL.md) describes the escape and a separate forced-call whitespace-stalling probe. The paper's description is correct. | BFCL AST prediction does not replicate live MCP task execution or that report's task-success result. |
| Toolhound | Its [pinned README](https://github.com/Code-byte404/toolhound/blob/97666be79a2af2afb78b36a168a5f89f84be6d97/README.md) reports trigger-gated MLX comparisons on a held-out custom suite, including Llama-3.2-3B at q4. The paper's description is correct. | A BFCL/llama.cpp result with a different prompt/compiler is a conceptual replication. The matched F16 control is an added comparison, not a reproduction of that q4 result. |

**Suggested resolution:** add a short prior-result/changed-components/contribution mapping and consistently call this a conceptual or mechanism-level replication. Do not claim to have resolved a contradiction between experiments that used different tasks and contracts. The manuscript currently avoids an explicit priority claim; preserve that restraint.

### M4 — Medium: several important settings are only discoverable in code or JSON

**Location:** §§3.1, 3.3, and 3.4; [prepare_full.py](scripts/prepare_full.py#L30), [full_runner.py](qunti/full_runner.py#L81), and [protocol.json](configs/protocol.json).

The PDF omits the BFCL **v4** dataset designation and dataset/checker revision, the bootstrap replicate count and seed, the actual operational seed labels, and the fact that Qwen uses `enable_thinking=False`. The frozen files do supply these: 10,000 bootstrap replicates, bootstrap seed 20261028, and operational labels 101/211/307/401/503. These omissions are reproducibility disclosures, not numerical contradictions.

Execution also uses one F16 load followed by one Q4 load per model, with the five schedules inside each precision block. Arms are shuffled within those blocks; precision order is not alternated. The paper correctly calls these operational repeats, but does not disclose that fixed precision order. Matching a GPU does not independently control time/order effects.

**Suggested resolution:** add a compact settings/provenance statement or a clearly linked appendix, explicitly identify non-thinking Qwen and precision order, and scope uncertainty to item/schedule variation under that execution. There is no evidence here that order caused the observed interaction; the limitation is that it was not separately tested.

### L1 — Low, inferential presentation: make the nominal nature of the negative headline explicit

**Location:** abstract, conclusion, Table 2, and §3.4.

The Llama-1B whole-strict result, −4.7 [−9.1, −0.3] points, supports a negative interaction under the stated pointwise interval. I did **not** find an unsupported direction claim at that nominal level. However, the abstract and conclusion say it “is negative” without repeating that the intervals are exploratory and unadjusted across the reported comparisons. The methods disclose this correctly. A reader should not infer a family-wise finding or a general law about quantized Llama models.

Also, none of the three free-decoding precision-loss intervals establishes positive quantization damage: Qwen 3.2 [−1.9, 8.3], Llama-1B −1.4 [−4.4, 1.4], and Llama-3B −2.0 [−4.6, 0.3] points. This limits a recovery-of-damage interpretation, but is not a reason to suppress null results. The paper properly withholds unstable/undefined recovery shares and rejects a causal syntax/semantics partition.

**Suggested resolution:** qualify the headline as an observed, pointwise negative interaction in this setup and explicitly note the absence of a resolved positive free-decoding loss. No recalculation is needed to make that wording precise.

## Numerical and claim coverage

The two requested Markdown reports do not contain every statistic printed in the PDF. I therefore checked their overlapping numbers directly, then traced the additional category, validity, contrast, and cost statistics to the companion JSON and raw files.

| Paper content | Audit performed | Result |
| --- | --- | --- |
| Setup counts and frozen subset | Reproduced item selection from the pinned upstream files and seed; checked category counts, 200 original items, 180 required-call items, five schedules and full factorial keys. | Matches; 24,000 unique primary observations, no missing or duplicated primary cell. |
| Official accuracy | Independently parsed every raw primary response under the declared contract and invoked the pinned upstream AST checker. Checked irrelevance behavior and incomplete-response policy separately. | Zero correctness mismatches against scored.jsonl. The upstream checker, evaluation runner, utility file, and parallel-data file were also re-fetched and byte-matched to the local copies. |
| Table 1 and REPORT.md | Checked all 24 required-call cells and their CIs; checked all 48 all-case/required-call estimate-and-CI entries in REPORT.md. | Exact agreement at displayed precision. |
| Table 2 | Checked all 27 free-loss/constrained-loss/recovery estimate-and-CI triplets and all share-status labels against saved estimates. | Matches; repeated free-loss columns are intentional, not additional independent estimates. |
| Primary uncertainty | Independently reproduced 144 cell/subset intervals and 66 loss/recovery/decoder-contrast intervals using crossed item/run resampling. | Matches the saved procedure and numbers. This checks implementation, not universal coverage of the bootstrap method. |
| Results prose and abstract | Checked all 27 prose interval triplets, absolute accuracy points, gains computed before rounding, headline recoveries and conclusion signs. | Matches. For example, the displayed 14.2% to 52.7% Llama-1B values accompany a 38.4-point gain because the gain uses unrounded scores; this is not an arithmetic mistake. |
| Figures 1–2 | Checked plotting inputs against the summary and inspected the embedded PDF figures against the tables. | No swapped models/precisions, clipped intervals, misleading axis scale, or plotted-value mismatch found. |
| Structure-validity claims | Independently validated all 6,000 whole-strict returned texts under the declared normalized-schema policy. | All satisfy that policy. This includes 11 token-limited whole-strict outputs with parseable structure; it does not mean every generation terminated normally. The paper's separate operational-failure treatment is important. |
| Failure counts | Checked the raw event inventory and every model/precision/arm breakdown. | 139 token limits and one replay error. All token limits report 512 predicted tokens, configured cap 512, and stop type `limit`. Replay error: Llama-1B/Q4/trigger-strict, `parallel_191`, seed 401. |
| Sensitivity results and limitations | Independently reproduced 144 exclusion cell/subset intervals, 54 recovery intervals and 36 decoder-contrast intervals; checked all 54 recovery rows in FAILURE_SENSITIVITY.md. | Matches. The reported unchanged interval interpretations hold, treating numerical round-off at zero as zero. |
| Exclusion denominators | Checked literal, matched-panel and complete-item retained counts across the full matrix. | Respectively 23,860, 23,336 and 23,200 observations. The latter two remove healthy counterparts too; they are not equivalent to dropping only 140 rows. |
| Cost paragraph | Independently summed the saved attributed billing rows and compared the forecast source and cap. | $2.61096875 rounds to the PDF's $2.6110; $4.74–$8.14 and the $12 cap match. Reported-to-date cost is correctly distinguished from a settled invoice. No live billing refresh was performed. |

The manuscript's main cautions are supported: CIs crossing zero are not treated as equivalence; schema-valid output is not equated with task correctness; negative incremental recovery is distinguished from a raw Q4 accuracy decrease; exclusions remain post-hoc; aborted batches are separate from the primary matrix.

One unresolved statistical specification question remains: sampling fixes category counts, whereas the bootstrap resamples across the pooled item set. The code accurately implements that pooled bootstrap. A reviewer may ask whether the inferential target is an empirical item mixture or a population with fixed category weights; the latter would motivate a stratified item bootstrap. I found no numerical inconsistency, and have not substituted a different estimand or interval scheme in this audit.

## Citation verification

All thirteen existing bibliography entries resolved to the stated work or software revision. Author/title metadata for the nine papers matched the primary records. The six pinned QuantCall/QuantMCP/Toolhound source files were re-fetched and matched their recorded SHA-256 values. The official llama.cpp pinned source also resolved. These checks establish source identity and the inspected claims, not independent reproduction of the prior experiments.

| Citation | Primary source | Claim assessment |
| --- | --- | --- |
| Flat Score [7] | [Jang et al., 2607.27275v1](https://arxiv.org/abs/2607.27275v1) | Aggregate success can hide process damage: supported. The manuscript does not misidentify its repair intervention as strict-schema decoding. |
| BF16 or Death [8] | [Kurtić et al., 2411.02355v4](https://arxiv.org/abs/2411.02355v4) | Recipe/workload dependence: supported. The 2024 entry uses the initial submission year; the linked v4 is a later revision, not a nonexistent paper. |
| Wu et al. [12] | [2608.06564v5](https://arxiv.org/abs/2608.06564v5) | Low-bit effects on tool-use decisions: supported. |
| StructureBench [13] | [Official IJCAI proceedings](https://ijcai.org/proceedings/2026/267) | Small-model structure/content separation: supported. |
| Chavan [5] | [2609.23742v1](https://arxiv.org/abs/2609.23742v1) | Structural validity versus content accuracy: supported. |
| Repair, Not Improvement [9] | [2608.13959v2](https://arxiv.org/abs/2608.13959v2) | Stopping versus restriction and paired item/seed inference: supported by the methods. |
| JSONSchemaBench [6] | [2501.10868v3](https://arxiv.org/abs/2501.10868v3) | Schema coverage and efficiency: supported. |
| Constraint Tax [10] | [2606.25605v1](https://arxiv.org/abs/2606.25605v1) | Serving/schema masks can suppress tool invocation: supported. |
| BFCL [11] | [Official ICML/PMLR record](https://proceedings.mlr.press/v267/patil25a.html) | Benchmark/checker attribution: correct; the executed v4 data revision still needs clearer identification in the paper. |
| QuantCall [2], QuantMCP [3], Toolhound [4] | Pinned primary reports linked in M3. | Existing descriptions are accurate; replication comparability needs clarification. |
| llama.cpp [1] | [Official pinned commit](https://github.com/ggml-org/llama.cpp/tree/8542e94350f0ade01644db6f1d1520da3814dafd) | Runtime attribution resolves correctly. |

## Scope and unchanged artifacts

This was a read-only audit of the manuscript, reports, raw primary outputs, scoring/analysis implementation, source provenance and release inventory. Temporary independent checking scripts, fetched primary-source files and rendered pages were kept under `/tmp/qunti-release-audit`, outside the repo. No public-release artifact was regenerated. `AUDIT.md` is the sole intended repository change and is not automatically included in the existing release archive.

I did not rerun the model experiments, independently reproduce the prior studies, establish family-wise statistical significance, certify bootstrap coverage, or determine a legal license for third-party data. The fixes above are recommendations, not changes already applied.
