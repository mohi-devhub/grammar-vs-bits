# Novelty gate — 2026-10-27

**Historical decision record:** the researcher subsequently requested continued gap analysis and alternative directions, without approving the proposed narrower question. See [DIRECTIONS.md](DIRECTIONS.md) for the current recommendation. The project is not shelved; implementation and cloud spend remain on hold pending the researcher's choice.

## Decision

**Hold implementation and paid compute; request a narrower contribution.** Direct prior work already tests the central idea. This is a novelty-risk judgement, not proof that every cell in the user's requested experiment has been published. No research question has been changed and no pilot has run.

The strongest direct overlap is [QuantCall's experiment report](https://github.com/Happynood/quant-toolcall-bench/blob/6b6e29e5c83a91a52bdfc68b5f3063de172c0e55/docs/constrained_decoding_findings.md): quantized models, BFCL-derived cases, separate structural/content metrics, and free versus GBNF decoding. Its README explicitly defines constrained-decoding recovery. [Toolhound](https://github.com/Code-byte404/toolhound/tree/97666be79a2af2afb78b36a168a5f89f84be6d97) also reports quantized small-model grammar comparisons and failure attribution. These are software reports, not papers; they still count when assessing a claim of novelty. Their runs were not independently reproduced in this review.

[StructureBench](https://ijcai.org/proceedings/2026/267) and [Chavan](https://arxiv.org/html/2609.23742v1) cover structural versus semantic correctness under constraints in small models. [Flat Score](https://arxiv.org/html/2607.27275v1) motivates process-level quantization diagnostics; its measured mitigation is reflexive repair, not the proposed full-schema intervention. [BF16 or Death](https://arxiv.org/html/2411.02355v4) supplies broad quantization context, not a tool-calling recovery answer.

## Why this is not a conclusive prior answer to our exact setup

- QuantCall's inspected default [grammar builder](https://github.com/Happynood/quant-toolcall-bench/blob/6b6e29e5c83a91a52bdfc68b5f3063de172c0e55/src/quantcall/decoding/gbnf.py#L96) unions a schema-shaped call with a branch accepting arbitrary text. Inference from the grammar language: a malformed call can also match the arbitrary-text branch, so full schema validity is not guaranteed. This inference does not establish which branch any particular prior generation used.
- Its report compares constrained results with a differently replicated free baseline. It does not establish the proposed paired, strict-schema study across all requested precisions and models.
- Toolhound's README reports grammar gains in a quantized condition; that alone does not identify the *incremental quantization loss* rescued relative to a matched full-precision constrained baseline.
- Chavan's listed evaluation models run in BF16. The paper is not a weight-precision sweep. Its function-call metric is also not the official BFCL AST checker.

Consequently: do not write “our exact experiment is already done,” but do not pitch “grammar fixes syntax but not all meanings in quantized tool callers” as an untouched finding.

## Recommended narrower question — awaiting approval

**Does weight quantization amplify sensitivity to the number of distractor tools, and does that interaction remain under tool-schema-constrained decoding?**

This promotes the user's tool-list-length stretch idea into the main contribution. Keep llama.cpp, the requested model families and GGUF precisions, temperature zero, and official BFCL AST scoring. Fix cache precision to FP16. Use a within-item design: keep the request, required tools, and accepted answers fixed while adding a deterministic, frozen set of irrelevant tools. Generate constraints only from the offered tools and their documented schemas.

The primary comparison would be the change in the FP16-to-quantized accuracy gap as distractors are added, evaluated separately for free and constrained decoding. Compare that interaction between decoding conditions. Measure function choice, argument errors, structural validity, truncation, and latency alongside accuracy. Resample original items with all their variants together.

Tool selection benefits from reducing the catalog are already established by [Less is More](https://arxiv.org/html/2411.15399v1). Its experimental setup also varies quantization recipes and retrieval sizes, so a precision-by-tool-count grid alone would not distinguish us. It changes the retrieved tool set and context configuration through a selection method. The narrower candidate contribution is a matched FP16 comparison on fixed distractor catalogs, especially whether the precision-by-catalog interaction persists under schema constraints. This limited search found no direct answer to that exact interaction; absence from this search is not proof of novelty. Before implementation, inspect the most relevant full texts and repositories again specifically for that interaction.

Catalog growth also increases token count and grammar complexity. Record those quantities, randomize/freeze tool order without using the answer key, and include a matched-length control if the pilot budget permits. Without such a control, conclusions concern catalog growth as a combined intervention, not a pure effect of tool count. Avoid selecting items because the baseline succeeds.

Keep the original pilot unchanged for runtime/cost calibration: one model × FP16/Q8_0/Q4_K_M × the same 50 frozen items × both conditions. A catalog-length extension is a separate, budgeted amendment after question approval; do not silently multiply pilot work. The full run still needs explicit approval after measured pilot costs.

## Alternative if a cache study is preferred

Hold weights at FP16 and vary only K/V cache precision in small-model BFCL calls, then measure structural errors and schema-constrained recovery. Pin both K and V formats and context length. This would replace, not silently augment, the weight sweep.

It also needs narrowing: [TriAxialKV](https://arxiv.org/html/2605.17170v1) already evaluates cache compression on BFCL Memory, and [Wu et al.](https://arxiv.org/html/2608.06564v5) examine cache-sensitive tool decisions. “First KV-cache study of agents” would be false.

## Search record and limits

Searched public web results on 2026-10-27 using combinations of:

```text
quantization function tool calling constrained decoding grammar LLM benchmark
"quantization" "constrained decoding" "tool" benchmark
"quantization" "function calling" grammar
"quantization" "tool calling" "syntactic" "semantic"
"quantization" "constrained decoding" "KV" tool calling
"quantization" "tool-list" length
"quantization" "tool list" benchmark
"quantization" "distractor" "tool" function calling
"KV cache quantization" "function calling" benchmark
"toolhound" github quantization
"TriAxialKV" arxiv
```

Followed citations from Flat Score to edge-function-calling work, checked official model pages, and inspected primary repository reports/source. Search snippets were used for discovery, not as evidence for technical claims. A Zenodo-titled lead discovered through an aggregator could not be verified at its primary record and is excluded from the bibliography. No claim is based on that lead.

GitHub's unauthenticated API was rate-limited; repository HEADs were resolved read-only with `git ls-remote` instead. Inspected repository file URLs and hashes are in SOURCES.json. The search is a practical novelty screen, not a systematic-review claim or an exhaustive guarantee.
