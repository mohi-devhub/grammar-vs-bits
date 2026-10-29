# Release v0.1.1 audit

Audited 2026-10-29 as a read-only review of the published artifacts. Only this report was added. Independent scoring and statistical checks used scratch files outside the repository. No model inference, cloud job, dependency installation, result regeneration, or manuscript rebuild was run.

**Verdict:** no High findings or performance-number mismatches found. The original findings have been addressed in substance. One Medium checksum-documentation issue and three Low clarity/reproducibility issues remain. The Pythonic sensitivity is explicitly separate from the primary matrix; I found no pooling of its outcomes into the primary results.

Release: [v0.1.1](https://github.com/mohi-devhub/grammar-vs-bits/releases/tag/v0.1.1), commit `16d4d2ed239cbaf7c523a3dd3d0d82684747bc5a`.

Audited PDF: six pages, SHA-256 `bdcd335f1dd6789e50ba5336935997c7a9828c8b204ff325a08ae3368bd17b81`. The published PDF digest matches the local PDF. The published archive digest matches the independently hashed local archive: `f990c86e904f2c8b2e8236fd059ca5a7730979fa48e04c944bfe6fa24c04f76b`.

## Findings, ranked by severity

### N-M1 — Medium: the appendix does not define the serialization used for its template checksum

**Location:** PDF p. 6, Appendix A; [settings_appendix.tex](paper/settings_appendix.tex), [prepare_full.py](scripts/prepare_full.py#L37), and [common.py](qunti/common.py).

The appendix calls `2732d9da5568668ed22ea202bffb12f0df405439651e1275ba1f521522f92966` the Llama template SHA-256. This reproduces the saved `chat_template_sha256` field, but it is **not** the SHA-256 of the template's UTF-8 text. The preparation script passes a string to `digest()`, which JSON-serializes it before hashing.

I checked both selected Llama tokenizer configurations, whose file hashes match the recorded configuration-file hash. Their template strings are identical and give:

| Hash input | SHA-256 |
| --- | --- |
| Template text encoded as UTF-8 | `5816fce10444e03c2e9ee1ef8a4a1ea61ae7e69e438613f3b17b69d0426223a4` |
| UTF-8 encoding of `json.dumps(template, sort_keys=True, ensure_ascii=False)` | `2732d9da5568668ed22ea202bffb12f0df405439651e1275ba1f521522f92966` |

**Consequence:** a reader hashing the actual template text will report a mismatch despite having the correct template. This is an undocumented hash-input convention, not evidence of different executed templates or corrupted scores.

**Suggested resolution:** state the exact serialization convention, or additionally publish and label the raw-text checksum. Preserve the historical recorded digest rather than silently changing provenance records. No model rerun is needed.

### N-L1 — Low: generic methods statements need an explicit primary-matrix qualifier

**Location:** PDF p. 2, §§3.1–3.3; [main.tex](paper/main.tex#L36).

The methods say that all arms and precisions for a model use one A10 worker, that all arms use `NO_CALL`, and that scoring adapts the declared JSON envelope. These describe the primary matrix. They do not describe the separate Pythonic sensitivity, which uses an AST call-list adapter and `[]`, and whose Llama-3B collection spans an interrupted worker and a continuation.

The sensitivity section correctly discloses those differences, including the 1,610/790 split. I found no concealed restart or combined primary/sensitivity denominator. The issue is that the earlier methods wording can be read as applying to the entire paper.

**Suggested resolution:** introduce §3 as the primary-matrix design, or qualify the affected sentences with “In the primary matrix.” Keep the sensitivity exceptions together with their own description.

### N-L2 — Low: the headline's precision-gap comparator has less uncertainty information than the format contrast

**Location:** PDF p. 1, abstract/introduction; [abstract_results.tex](paper/generated/abstract_results.tex), [intro_finding.tex](paper/generated/intro_finding.tex).

The 6.0- and 3.3-point Pythonic F16-to-Q4 whole-strict gaps are correct paired point estimates on the same 60 parallel items. The abstract prints CIs for the format gains but no paired CIs for these precision gaps. Under the same crossed item/run resampling, I obtain approximately **6.0 [−4.7, 16.7]** and **3.3 [−0.7, 8.7]** points. These intervals are additional audit calculations, not numbers currently printed in the paper.

This does not invalidate the stated comparison of **observed** magnitudes. The paper also correctly rejects a general law about quantization and a parser-only causal interpretation. It would nevertheless help readers to see that the precision-gap comparators are uncertain estimates, rather than bounds on quantization harm.

**Suggested resolution:** add the paired precision-gap intervals or a clearly linked comparator table. Retain the existing “observed,” setup-specific wording; do not turn the result into a claim that quantization is irrelevant.

### N-L3 — Low: the standalone PDF does not identify its exact release version

**Location:** PDF p. 6, Appendix A; [settings_appendix.tex](paper/settings_appendix.tex).

The public repository link works and the primary campaign is identified as `full-002`. However, the PDF does not print `v0.1.1`, its source commit, or a versioned release URL. The primary campaign ID alone cannot distinguish this reframing from the earlier paper about the same campaign.

**Suggested resolution:** add the versioned release link or source commit, and identify `pythonic-002` as the sensitivity campaign. The original inability to locate any artifacts is fixed; this remaining issue concerns locating the exact historical version from a standalone PDF.

## Resolution of the original AUDIT.md findings

| Original finding | Status in v0.1.1 | Evidence checked |
| --- | --- | --- |
| H1: misleading native-contract description | Resolved in substance | §3.2 identifies the HF single-object JSON branch, `tools_in_user_message=True`, added parallel-array convention and conflicting later instruction. Primary Llama conclusions are conditional on that contract. The alternative Pythonic study is separate. Both frozen prompt bundles support the description. See N-M1 for the checksum convention. |
| H2: missing executed Qwen source | Resolved | The archive contains the exact Qwen worker files and original hash record under `provenance/executed-workers/full-002-1/`. Independently verified all 56 archived worker files across six submissions, including the interrupted sensitivity worker and continuation. Maintained source is separate. Unretained historical launcher versions are explicitly acknowledged. |
| H3: absent licenses/attribution | Resolved for the identified release omissions | MIT license, Gorilla Apache-2.0 license, BFCL attribution and transformation notices are present in the actual archive. The shipped upstream license byte-matches its pinned official source. The packager includes these files. |
| M1: no artifact URL/public-registration ambiguity | Core issue resolved | The availability URL is public and works. The paper says “frozen before execution” and explicitly says there was no public preregistration timestamp. N-L3 recommends a version-specific link. |
| M2: omitted relevant citations | Resolved | Added Zhang et al., Tang and Zheng, Meta prompt documentation and Qwen3 publisher documentation. The new paper titles/authors match their primary records; the Meta documentation supports the Pythonic call-list form. No new fabricated or misidentified citation found. |
| M3: unclear replication mapping | Resolved | Table 1 names QuantCall, QuantMCP and Toolhound, describes changed components and confirmation criteria, and labels the work conceptual. It does not claim reproduction of live MCP task success or prior numerical scores. The three pinned reports re-fetched for this audit match the previously inspected bytes. |
| M4: missing reproducibility settings | Resolved for the original settings omissions | Appendix A supplies BFCL v4/revision, engine revision, bootstrap 10,000/seed 20261028, operational labels, Qwen non-thinking mode and fixed F16-then-Q4 order. These match the saved configuration. N-M1 concerns the newly supplied template checksum's input convention. |
| L1: overly broad inferential headline | Resolved | The abstract/conclusion scope intervals as pointwise, unadjusted and setup-specific. No primary free-decoding precision-loss interval excludes zero. New inconclusive-recovery statements explicitly concern sensitivity parallel items, rather than erasing the primary Llama-1B negative interaction. |

The citation checks included the primary records for [TOOLDEC](https://arxiv.org/abs/2310.07075v3), [Tang and Zheng](https://arxiv.org/abs/2609.26693v1), and [Meta's pinned prompt documentation](https://github.com/meta-llama/llama-models/blob/0e0b8c519242d5833d8c11bffc1232b77ad7f301/models/llama3_2/text_prompt_format.md). The inspected software sources were the pinned [QuantCall report](https://github.com/Happynood/quant-toolcall-bench/blob/6b6e29e5c83a91a52bdfc68b5f3063de172c0e55/docs/constrained_decoding_findings.md), [QuantMCP report](https://github.com/Happynood/quant-mcp-bench/blob/fc98a47c6a0ef77bb8be3a915016b42d203faf45/docs/RUN_REAL.md), and [Toolhound README](https://github.com/Code-byte404/toolhound/blob/97666be79a2af2afb78b36a168a5f89f84be6d97/README.md). This verifies source identity and the stated scope, not independent reproduction of their experiments.

## Independent numerical checks

### Primary results

The primary raw outputs, scored outputs, summary, operational-failure sensitivity and published numeric tables are byte-identical to v0.1.0. I also independently parsed and scored all 24,000 primary outputs with the pinned official AST checker: **zero correctness mismatches**. The local checker bytes match the pinned official source.

Recomputed all 144 primary cell/subset intervals, the 144 exclusion cell/subset intervals, 54 exclusion recovery intervals and 36 exclusion decoder-contrast intervals checked by the independent harness. All match. The current PDF's Table 2 has 24 matching accuracy cells; Table 3 has 27 matching estimate-and-CI triplets. The original failure inventory remains 139 token limits and one replay error.

### Separate Pythonic sensitivity and reframed claims

Independently parsed and scored all **4,800** sensitivity outputs: **zero correctness mismatches**. The checkpoints contain 2,400 Llama-1B outputs and disjoint sets of 1,610 and 790 Llama-3B outputs, with no duplicate or missing matrix keys. Recorded weight-artifact hashes match the primary campaigns; model revisions, A10 allocation and frozen input/prompt/grammar hashes also match the declared sensitivity setup.

The original 60 parallel cases, including inputs and accepted answers, are unchanged. The extra 60 parallel-multiple cases have no primary JSON comparison and are not used in the headline comparison.

| Matched parallel endpoint | Llama-1B | Llama-3B |
| --- | --- | --- |
| JSON Q4 whole-strict successes | 3/300 = 1.0% | 0/300 = 0.0% |
| Pythonic Q4 whole-strict successes | 187/300 = 62.3% | 265/300 = 88.3% |
| Pythonic Q4 accuracy CI | [50.0, 74.3]% | [80.0, 95.7]% |
| Paired Pythonic-minus-JSON gain | 61.3 [48.7, 73.3] points | 88.3 [80.0, 95.7] points |
| Pythonic F16 whole-strict successes | 205/300 = 68.3% | 275/300 = 91.7% |
| Pythonic F16-to-Q4 whole-strict point gap | 6.0 points | 3.3 points |
| Pythonic incremental recovery | 1.7 [−10.3, 13.7] points | −3.3 [−8.7, 0.7] points |
| Change in incremental recovery versus JSON | 2.3 [−10.0, 15.0] points | −3.3 [−8.7, 0.7] points |

All match the abstract, introduction, conclusion and sensitivity section at displayed precision. I reproduced all **40** saved sensitivity intervals: 24 cell intervals, eight protocol contrasts, six recovery effects and two protocol changes in recovery.

The evidence supports a large **observed joint-contract contrast on these matched items**. It does not isolate syntax, establish a pure format-only causal effect, or establish positive quantization-specific recovery. The manuscript states these limits, discloses different sessions/time/hosts and the worker restart, and does not merge the sensitivity into the primary matrix. I found no unsupported positive-recovery or universal quantization claim.

### The 578-limit table on p. 4

The printed table matches the raw outputs exactly:

| Model | F16 free | F16 whole strict | Q4_K_M free | Q4_K_M whole strict | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Llama-1B | 146 | 65 | 284 | 64 | 559 |
| Llama-3B | 5 | 5 | 4 | 5 | 19 |
| Total | 151 | 70 | 288 | 69 | 578 |

Each cell covers 120 cases × five operational labels = 600 observations. This is the full sensitivity cohort, not just the headline's 60 parallel cases. Of the 578 limits, 213 occur on those matched parallel cases; the remaining 365 occur on parallel-multiple cases. In the headline's Pythonic Q4 whole-strict cells specifically, there are 16 limits for 1B and none for 3B.

Every token-limit output reports 512 predicted tokens and stop type `limit`, has `completed=False`, and is scored incorrect. Therefore the quoted failure-inclusive gains already include their penalty. This supports the paper's fixed-cap conclusion; it does **not** establish what would happen with longer generation or after excluding incomplete outcomes. The paper correctly says no added exclusion analysis is claimed. No token-limit count or treatment mismatch found.

## Release, links and remaining boundaries

- Independently checked the archive's embedded inventory, all **1,984** member hashes, and their corresponding working-file hashes. The PDF and archive match GitHub's published asset digests, and the release tag points to the audited commit.
- The new cost paragraph's $0.7346 additional and $3.3456 project totals match the saved billing snapshot, including failed/interrupted apps. These are historical reported-to-date values; no live billing refresh was performed.
- Rechecked all **18 unique external PDF URLs** using HTTP requests: all resolve. The former repository URL redirects with HTTP **301** to the canonical repository. No broken PDF link found. The current Qwen publisher citation opens its pinned file tree; its README/model card is accessible there.
- The sensitivity remains a separate post-primary analysis of a changed contract. Its large gain is not a replacement primary score or a replication of Meta's complete prompt verbatim; the instructions are paraphrased and `[]` is a declared study convention.
- The earlier audit's pooled-versus-stratified bootstrap question remains a specification limitation, not an arithmetic discrepancy. The headline's matched parallel endpoint avoids mixing the two sensitivity categories, but the paper still does not fully define the population target for pooled multi-category intervals.

No existing repository file was changed during this audit. The original AUDIT.md and all released artifacts remain intact.
