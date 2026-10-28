# Protocol and interpretation notes

Direction 1 completed its approved full run. The fixed protocol is in configs/protocol.json; [FULL_REPORT.md](FULL_REPORT.md) links the saved scores, confidence intervals, costs and integrity checks. These notes specify the interpretation used throughout collection and analysis.

## What recovery measures

Let A(p,d) be official BFCL item accuracy at weight precision p and decoding condition d, with f denoting free generation and c denoting tool-schema constraints. Define:

```text
L_free(q)        = A(FP16,f) - A(q,f)
L_constrained(q) = A(FP16,c) - A(q,c)
net_recovery(q)  = L_free(q) - L_constrained(q)
recovery_share  = net_recovery(q) / L_free(q)
```

This subtracts the benefit or harm constraints already have at FP16. Dividing the quantized model's raw constrained gain by free-decoding loss would incorrectly count that baseline effect as recovery of quantization damage.

**The recovery share is an intervention effect, not an identified fraction of exclusively syntactic damage.** A tool schema can prevent hallucinated function names, unknown keys, and invalid types as well as invalid JSON. It changes the possible continuations and can alter subsequent choices. A constrained success following a free failure therefore does not prove the original error was “only syntax.” Likewise, a residual failure can be caused by truncation, an unsupported schema, or a harness problem rather than semantics.

Always report the signed accuracy differences first. Report the ratio as undefined when the estimated free loss is nonpositive; flag an interval spanning zero as an unstable denominator rather than produce a headline percentage. Keep out-of-range ratios visible when interpretable; do not clip them to manufacture a partition. Paired item transitions and observable error rates support a narrower interpretation than a causal decomposition of model knowledge.

A separate JSON-only grammar arm could help distinguish JSON formatting from schema enforcement, but it is an additional condition requiring an explicit protocol/budget amendment. It is not silently added to the requested two-condition pilot.

## Grammar and prompt contract

- Use identical rendered prompts within a precision/condition comparison, recording tokenizer and chat-template hashes. Change only the decoder constraint between free and constrained arms.
- Derive constraints from the entire offered tool catalog and documented schemas. Never consult reference answers, the expected tool, accepted argument values, or gold call counts when constructing the grammar.
- Allow arrays/sequences for parallel calls without forcing the reference number or order of calls. Decide the output envelope once and apply it in both arms. If the selected benchmark requires a call, any restriction on empty calls must be stated as an assumption about that subset, not silently inferred per answer.
- The selected loose arm deliberately includes an arbitrary-text escape as a conceptual-replication control; it provides no validity guarantee. The two strict arms must not include that escape. Handle unsupported JSON Schema features explicitly. Independently validate generated calls and record the schema and grammar bytes/hashes per item.
- Use the same token/context limits and stop rules in both arms. Reject overlong inputs before inference. Log token-limit termination and whitespace/repetition failures separately from successful constrained output.

The official [llama.cpp GBNF guide](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md) documents the schema conversion support and limitations. The implementation is pinned to 8542e94350f0ade01644db6f1d1520da3814dafd; this moving documentation URL is explanatory, not the runtime pin. The offline gate tests both declared JSON envelopes and all selected schemas. The pilot exercises free and whole-strict serving; the full worker separately checks lazy trigger replay with synthetic literal probes before collection.

## Deterministic errors and official scoring

Use the pinned official BFCL AST checker as the accuracy authority. Convert the chosen JSON call envelope into the checker's expected representation without executing generated code. Keep conversion failures distinct from model failures. The AST checker's accepted values/normalization rules must govern success; a custom exact-match checker is insufficient.

For diagnostics, store multiple error flags and an explicitly ordered primary label; “wrong function” and “hallucinated function” are otherwise overlapping. Distinguish an existing but wrong offered tool from a nonexistent tool; likewise distinguish an argument belonging to another offered tool from a wholly unknown key. Report conditional argument diagnostics only when a meaningful function/call alignment exists. Use official accepted-reference alternatives so a valid alternative is not labelled a wrong value. Specify deterministic matching for unordered parallel calls, duplicates, and missing/extra calls. Treat any missing/extra-call flag as an auxiliary diagnostic, not an unannounced change to the requested taxonomy.

Record format/JSON parse failure, wrong function, missing/extra args, wrong arg type, wrong arg value, and hallucinated function/args. Also record schema compilation failures, runtime failures, context overflow, truncation, and timeouts as operational statuses. Publish attempted and evaluable denominators and a fixed failure policy; do not quietly drop hard items.

## Pairing and uncertainty

Freeze seed, item IDs, category counts, source revisions, and input hashes before inference. Use the same items in every cell; make the pilot a documented subset. Temperature zero is greedy decoding, not a guarantee of bit-identical GPU runs under changing batching. Pin concurrency and server flags, record slot/batch metadata, disable uncontrolled cache reuse, and reserve a small repeat check if affordable.

Bootstrap item IDs once per replicate, retaining all model/precision/condition observations of each selected item. If catalog-length variants are approved, keep all variants of the original item together. Report paired difference intervals and intervals for category rates, not significance inferred from overlap of marginal intervals. Predeclare the primary comparison and label other cells exploratory; a small frozen subset can yield wide intervals and limited generalization.

Model GGUF metadata must distinguish FP16, mixed K-quant formats, tensor-type mixtures, and actual file sizes. Produce each quant directly from the same FP16 export rather than requantizing a lower-precision file. Keep K and V cache formats fixed in the weight experiment. Record model revision, conversion settings, quantization command, llama.cpp commit/build flags, GPU, seed, condition, UTC date, request/response, token counts, timing, and server metadata with every run.
