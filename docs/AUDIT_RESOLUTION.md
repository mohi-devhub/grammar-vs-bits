# Audit resolution

The dated AUDIT.md is preserved as the review record. This document describes the changes made in response; it does not replace or rewrite the original primary results.

| Finding | Resolution | Evidence |
| --- | --- | --- |
| H1 | The paper identifies the pinned HF tokenizer_config.json JSON branch, tools_in_user_message=True, template hash, added system JSON-array convention and conflicting later single-object instruction. Llama conclusions are scoped to that contract. Meta's documented Pythonic list is cited. | paper/main.tex §3.2; settings appendix; frozen original prompts remain unchanged. |
| H2 | Exact executed worker snapshots and original hash records for every complete primary model session are shipped under provenance/. The maintained code remains in root qunti/. Historical launcher revisions were not retained; that limit is explicit. | provenance/executed-workers/manifest.json; scripts/verify_provenance.py. |
| H3 | MIT license for original code; pinned upstream Gorilla Apache-2.0 license, BFCL attribution and transformation notice. The archive allowlist includes license, notices and provenance. | LICENSE; THIRD_PARTY_NOTICES.md; third_party/gorilla/; scripts/package_release.py. |
| M1 | Public repository created at https://github.com/mohi-devhub/qunti-check. Paper appendix and README link it. Current claims use “frozen before execution” and explicitly disclaim a public preregistration timestamp. | paper/settings_appendix.tex; README.md. Historical raw fields and executed source are preserved rather than rewritten. |
| M2 | Added TOOLDEC (Zhang et al.), serving-stack confounds (Tang and Zheng), Qwen3 model card and Meta prompt documentation. | paper/references.bib; docs/BIBLIOGRAPHY_METADATA.json. |
| M3 | Study consistently described as a conceptual replication. A table maps prior work, changed components, and what would count as mechanism-level confirmation. It does not claim reproduction of live MCP success or prior numerical scores. | paper/replication_table.tex. |
| M4 | Compact appendix gives BFCL v4/checker revision, engine revision, bootstrap draws/seed, operational labels, Qwen non-thinking mode and fixed F16-then-Q4 order. | paper/settings_appendix.tex; source settings remain frozen. |
| L1 | Abstract and conclusion explicitly scope intervals to this setup, pointwise and unadjusted, and note that no free-decoding precision-loss interval excludes zero. | Generated abstract/conclusion from scripts/build_paper_data.py. |

## Separate optional format sensitivity

The separately approved Pythonic study retains its own frozen data, raw outputs and analysis. Its design uses the original parallel cases plus a new deterministic parallel_multiple subset. It changes the joint prompt/parser/grammar contract, omits the HF single-object tools injection, and uses an empty list for abstention. Only the overlapping parallel cases support a matched comparison with the primary JSON contract. This study is not pooled into the original matrix and is not the planned Direction 2 intervention study.

The first optional launch failed at module import before generation; its app was stopped and its log/cost retained. The replacement explicitly packages that module. Llama-3B then lost its worker to a reported platform internal failure, with the precise cause unconfirmed. Its 1,610 saved outputs were retained; only the missing 790 cells continued on another A10. The complete separate design has 4,800 unique observations, including 578 token-limit outcomes counted as incorrect. Original interruption state, disjoint checkpoints, source snapshots and all app costs remain released. No unavailable outcome is treated as a zero cost or a successful prediction.

## Release verification

The final archive is checked against an embedded per-file SHA-256 inventory, including exact executed-source hashes and license presence. Model weights, credentials and runtime caches are excluded. Dependency auditing remains clean with the pinned lockfiles. The final verification artifact records the actual PDF page count, checksums, tests, unchanged primary-result hashes, optional-study status and app shutdown evidence.

## Measured sensitivity outcome

- meta-llama/Llama-3.2-1B-Instruct: original parallel Q4 whole-strict accuracy 1.0% → 62.3%. Paired gain 61.3 points [48.7, 73.3].
- meta-llama/Llama-3.2-3B-Instruct: original parallel Q4 whole-strict accuracy 0.0% → 88.3%. Paired gain 88.3 points [80.0, 95.7].

This changes the interpretation of the low Llama parallel scores: the declared contract matters strongly. Neither Pythonic parallel incremental recovery nor its change relative to JSON is resolved from zero. This does not change the primary 180-item estimates or isolate a parser-only causal effect. The follow-up has condition-dependent token limits and a disclosed worker restart; no added exclusion analysis is claimed.

Reported additional app cost is $0.734616 against $3; latest project metering is $3.345584 against $12. These are reported-to-date values, including failed/interrupted apps, rather than a settled invoice. results/ops/audit-fixes_final_shutdown.json confirms zero active project apps and containers. Regenerable weight caches were removed after preserving all sensitivity provenance. Direction 2 remains planned and unevaluated.
