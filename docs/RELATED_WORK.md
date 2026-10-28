# Related work

Checked 2026-10-27. Links below are primary sources. The original design is a proposal, not a completed experiment. “Difference” describes a possible distinction, not a claim of priority. The two requested papers were read in their main text plus limitations; other paper entries use the linked abstract, proceedings page, or identified methods sections.

## Quantization and tool use

**Jang et al., “Flat Score, Amplified Failures: How the Error Budget Masks Damage in Quantized LLM Agents” (2026), [arXiv:2607.27275v1](https://arxiv.org/html/2607.27275v1), Setup, Results, Discussion, Appendices B–C.**
Shows that aggregate task success can hide increased tool-name failures in quantized multi-turn agents; evaluates reflexive repair, while discussing constrained decoding as a mitigation.
Difference: our proposed small-model GGUF/BFCL study would measure decode-time schema constraints directly, without a multi-turn simulator or retry budget; error decomposition itself is already established.

**Kurtić et al., “Give Me BF16 or Give Me Death”? Accuracy-Performance Trade-Offs in LLM Quantization (2024; revised 2026), [arXiv:2411.02355v4](https://arxiv.org/html/2411.02355v4), §§3–5 and Limitations.**
Evaluates tuned quantization recipes for accuracy, latency, and throughput across general, code, long-context, and reasoning tasks; configuration and workload matter to the conclusions.
Difference: it does not provide the proposed tool-call syntax/content decomposition or a free-versus-schema-constrained GGUF experiment; its broad “near-lossless” findings cannot establish tool-call robustness.

**Paramanayakam et al., “Less is More: Optimizing Function Calling for LLM Execution on Edge Devices” (arXiv 2024; DATE 2025), [arXiv:2411.15399v1](https://arxiv.org/html/2411.15399v1), abstract, methodology, and experimental setup/results.**
Proposes selecting fewer tools for edge function calling and evaluates multiple quantization variants and retrieval sizes; reducing tool sets in quantized models is already studied.
Difference: a narrower study would need matched FP16 controls, fixed distractor catalogs, and the precision-by-catalog interaction under schema constraints. A quantization-by-tool-count grid alone is insufficient novelty.

**Wu, Dhiman, and Koshiyama, “Which Decisions Low-Bit Quantization Breaks, and How to Predict Them” (2026), [arXiv:2608.06564v5](https://arxiv.org/html/2608.06564v5), abstract, §4.3, and Appendix A.19.**
Studies decision-margin changes under multiple quantizers, including GGUF, and distinguishes whether-to-call, which-tool, and call-formation failures on BFCL; also studies cache precision.
Difference: a small-model study must add a controlled interaction or intervention, not claim to discover that tool-call damage has multiple causes. The identified sections do not establish our full-schema recovery matrix.

## Constraints, structural validity, and content accuracy

**Zhang et al., “Don't Fine-Tune, Decode: Syntax Error-Free Tool Use via Constrained Decoding” (2023; revised 2024), [arXiv:2310.07075v3](https://arxiv.org/abs/2310.07075v3), abstract.**
Introduces TOOLDEC, using finite-state constraints to enforce tool syntax and improve tool use without fine-tuning.
Difference: quantization-specific recovery is not established by its abstract; syntax repair through constrained decoding is prior art and cannot be our standalone novelty claim.

**Geng et al., “JSONSchemaBench: A Rigorous Benchmark of Structured Outputs for Language Models” (2025), [arXiv:2501.10868v3](https://arxiv.org/abs/2501.10868v3), abstract.**
Evaluates constrained generation for efficiency, schema coverage, and output quality, including llama.cpp among the frameworks.
Difference: the proposed study varies quantization and uses tool-call task accuracy; schema compilation/coverage needs validation rather than an assumption that every schema is supported.

**Xiong et al., “StructureBench: A Unified Benchmark Suite for Multi-Scenario Structured Generation Tasks with On-Device Models” (IJCAI 2026), [official proceedings](https://ijcai.org/proceedings/2026/267), abstract.**
Separates structural validity and semantic correctness for small on-device models, including tool calling, and finds that constraints can preserve structure without improving content.
Difference: the proposed contribution must be a quantization-specific interaction; the structural-versus-semantic distinction and small-model setting already overlap directly.

**Chavan, “Constrained Decoding Eliminates Structural Failures in Small LLMs but Reveals a Scale-Dependent Semantic Gap” (2026), [arXiv:2609.23742v1](https://arxiv.org/html/2609.23742v1), §§3–4.**
Compares native, Outlines, and XGrammar decoding on a small structured-output task suite; the listed models run in BF16, and function-call scoring includes function choice and required-parameter presence.
Difference: varying weight precision and using the official BFCL AST checker would extend it; constrained recovery of structure without complete content recovery is already its central finding.

**Li, Zhang, and Lv, “Constraint Tax in Open-Weight LLMs: An Empirical Study of Tool Calling Suppression Under Structured Output Constraints” (2026), [arXiv:2606.25605v1](https://arxiv.org/abs/2606.25605v1), abstract.**
Reports tool suppression when tool calling and response-schema constraints interact; token masks can exclude tool-call tokens, motivating a two-pass execution strategy.
Difference: this is a serving-contract confound, not evidence of quantization loss; our constrained arm must constrain the intended call representation and preserve all allowed actions.

**Lee, “Repair, Not Improvement: Decomposing Constrained Decoding in Tool-Call Abstention” (2026), [arXiv:2608.13959v2](https://arxiv.org/abs/2608.13959v2), abstract; v1 main text also inspected.**
Separates stopping behavior from restrictions on tool-name choices and shows why grammar interventions can harm abstention.
Difference: our original subset concerns required calls, not bilingual abstention; we must still avoid reference-derived call counts, gold tool restrictions, or treating a changed stop rule as a syntax-only effect.

## KV-cache alternative and benchmark

**Shen et al., “TriAxialKV: Toward Extreme Low-Precision KV-Cache Quantization for Agentic Inference Tasks” (2026), [arXiv:2605.17170v1](https://arxiv.org/html/2605.17170v1), abstract and §4.**
Develops mixed-precision cache compression and evaluates BFCL Memory and OSWorld, including the sensitivity of system/tool-schema segments.
Difference: “KV quantization affects agents” is already covered. A narrower cache-only proposal would need to isolate syntax/content recovery under constraints in small models, not claim cache quantization in tool use is unstudied.

**Patil et al., “The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models” (ICML 2025), [official proceedings](https://proceedings.mlr.press/v267/patil25a.html) and [official evaluation introduction](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html).**
Introduces tool-use evaluation with AST-based matching and executable checks; AST scoring checks function names and arguments against accepted references, not just parseability.
Difference: we would use its official checker on a frozen subset, adding precision and decoding conditions rather than presenting a new benchmark or replacing its semantics with exact string matching.

## Directly overlapping software projects (not papers)

**Happynood, QuantCall / quant-toolcall-bench, [repository](https://github.com/Happynood/quant-toolcall-bench/tree/6b6e29e5c83a91a52bdfc68b5f3063de172c0e55), [constrained-decoding findings](https://github.com/Happynood/quant-toolcall-bench/blob/6b6e29e5c83a91a52bdfc68b5f3063de172c0e55/docs/constrained_decoding_findings.md).**
Already implements GGUF/BFCL tool-call degradation, separate schema/argument metrics, and a constrained-decoding recovery metric, with reported free-versus-GBNF GPU experiments.
Difference/limit: its default grammar admits unrestricted text, so the reported null does not settle strict schema enforcement; constrained runs also have fewer seeds. Our exact model/quant/checker matrix is not established by this project, but the central experimental idea overlaps directly.

**Happynood, QuantMCP / quant-mcp-bench, [repository](https://github.com/Happynood/quant-mcp-bench/tree/fc98a47c6a0ef77bb8be3a915016b42d203faf45), [run report](https://github.com/Happynood/quant-mcp-bench/blob/fc98a47c6a0ef77bb8be3a915016b42d203faf45/docs/RUN_REAL.md).**
Extends schema-validity versus actual-outcome analysis to real MCP schemas, quantization sweeps, and constrained decoding; reports negative recovery and whitespace degeneration.
Difference: fixed BFCL calls would avoid live MCP execution but would not make syntax-versus-task-success or negative grammar recovery a new observation.

**Code-byte404, Toolhound, [repository](https://github.com/Code-byte404/toolhound/tree/97666be79a2af2afb78b36a168a5f89f84be6d97), README and bundled report description.**
Attributes failures to templates, parsers, model formatting, or model decisions, and reports free/constrained comparisons on quantized small Qwen/Llama models.
Difference: it uses MLX and a custom suite, not our planned llama.cpp/BFCL factorial study; the explanatory headline that grammar rescue depends on the failure layer is already present. Its CI-overlap rule is not a substitute for a paired-difference CI.

## Assessment

The broad question is already investigated, including direct quantization-plus-grammar experiments. The exact requested fully constrained BFCL matrix was **not verified as already answered**; prior limitations leave room for a careful extension, not a “first study” claim. See [NOVELTY_CHECK.md](NOVELTY_CHECK.md) for the decision and an unapproved narrower proposal. No empirical claim here is an outcome of this project.
