# Learning notes

The offline gate and model preparation are complete. The retried pilot completed all 300 generations on one NVIDIA A10. The completed full-study findings are in docs/FULL_REPORT.md and the generated section below. See the dated current-status section below; the conceptual explanations are not measured accuracy claims.

## What quantization formats mean

A model stores learned numerical weights. Quantization represents many of them with a smaller set of values, reducing storage and memory traffic while introducing approximation error. The effect on a generated answer depends on which token choices change; it need not produce a smooth accuracy decline.

FP16 and BF16 are different floating-point formats with different precision/range trade-offs. Our requested reference is an FP16 GGUF export. Keep that exact export as the common source for quantization and comparison; do not casually rename it BF16 because the downloaded model was originally stored that way.

GGUF is a model file/container format. Q8_0 is a blockwise weight-quantization format; Q6_K, Q4_K_M, Q3_K_M, and Q2_K describe other llama.cpp quantization recipes. Their labels indicate nominal precision and recipe families, not an exact uniform number of bits for every parameter. Scaling metadata and mixtures of tensor formats affect real file size and quality. Record the actual tensor types and file hashes in the release. The official [llama.cpp repository](https://github.com/ggml-org/llama.cpp) is the implementation authority to pin before running.

Weight quantization changes stored model parameters. KV-cache quantization changes the stored attention state produced while processing a particular context. They are separate interventions; keeping the cache fixed is necessary to interpret a weight-only experiment.

## Why constraints can fix formatting without guaranteeing meaning

A constrained decoder masks tokens that would make the output violate a grammar. A JSON grammar can prevent an unfinished object; a tool schema can additionally restrict names, required keys, and types. The official [GBNF guide](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md) explains this mechanism and the supported schema conversion.

For example, a schema can require a `city` string in a `weather` call. Both `"Paris"` and `"London"` can satisfy that schema. Only the user's request determines which is correct. An enum of offered tools can exclude an invented name while still allowing the wrong real tool. Constraints can influence which allowed choice wins, so “they cannot guarantee meaning” is more accurate than “they never change meaning.”

Structural validity includes schema rules; JSON syntax is a narrower property. We should measure them separately and avoid calling every accuracy improvement “syntax recovered.”

## How BFCL scoring works

[BFCL's official introduction](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html) describes AST matching and executable checks. Our frozen subset uses the official AST checker: it represents calls structurally and checks function names and arguments against accepted answers under its evaluation rules. It is not just a JSON parser and not an LLM judge.

“Simple” asks for a call from a simple tool setting; “multiple” requires selecting among offered functions; “parallel” requires multiple calls. The exact frozen category definitions and checker revision must come from the pinned upstream release. Parallel matching and accepted alternative argument values make a homemade string comparison an unreliable replacement.

We retain official correctness as the headline metric and use our deterministic taxonomy to explain failures. If our taxonomy calls an output wrong that the official checker accepts, we investigate the disagreement rather than override the reference score.

## How to read the results

Compare each quantized model with its matched FP16 baseline on the same items. If both free and constrained accuracies fall similarly, constraints have not recovered the measured quantization gap. If the constrained gap is smaller, the intervention has recovered some measured loss. The interpretation still depends on observable errors, completion limits, and the schema's restrictions.

We subtract the constraint effect already present at FP16. Otherwise we could mistakenly attribute a general formatting benefit to quantization repair. See [the estimand](docs/PROTOCOL_NOTES.md).

A confidence interval describes uncertainty under resampling this item population; it does not prove that the result applies to all tools or deployment stacks. Keeping the same resampled items across conditions preserves the paired comparison. An interval containing zero means the experiment does not establish the direction of the effect at that precision; it does not prove identical behavior. A tiny or absent baseline loss makes a recovered-*share* ratio unstable or undefined.

Null and negative results are useful: constraints may have little room to help, may redirect errors toward wrong valid calls, or may cause incomplete outputs. Those possibilities must be distinguished with logs, not guessed from the final accuracy alone.

## Explain this in 2 minutes

“We want to know what goes wrong when a small tool-using language model is compressed. A tool call needs the right format, the right function, and the right arguments. Smaller numerical representations might affect any of those.

“We ran the same requests at full and reduced precision, then repeated them with a decoder that only permits calls following the documented tool schemas. The benchmark's official checker decides whether each call answers the request. Our diagnostic labels explain whether it failed to parse, picked an incorrect function, or supplied incorrect arguments.

“A valid-looking call can still do the wrong thing. Also, grammar constraints help full-precision models too, so that baseline benefit has to be subtracted before claiming recovery of compression damage. We compare paired items and show uncertainty, including when no damage or recovery is measurable.

“We ran a conceptual replication of permissive versus strict tool-call constraints. The full study is complete. Strict constraints produced valid structures, but correct structure did not guarantee the right calls or arguments. To measure quantization-specific recovery, we subtracted the benefit constraints already gave the higher-precision model. That comparison did not establish consistent positive recovery. The confidence intervals are pointwise and apply to this setup. Llama used a declared JSON contract with conflicting parallel-call instructions, so its low parallel score cannot establish an intrinsic inability. A separately frozen Pythonic-format sensitivity checks that concern without replacing the primary results.”

## Five interview questions and answers

1. **Why use the same inference engine for every precision?** To reduce confounds from chat templates, tokenization, output parsers, and runtime defaults. We would convert the same checkpoint and pin the engine build and settings.

2. **Does schema-valid output mean correct tool use?** No. A call can use a real function and correctly typed arguments but select the wrong function or wrong values for the request. The official task score checks more than validity.

3. **Why also constrain the FP16 baseline?** It identifies how much constraints help independently of quantization. Recovery of incremental quantization loss compares the precision gaps under both decoding conditions.

4. **Why bootstrap items together across conditions?** The same hard request can fail in several cells. Preserving those relationships makes the uncertainty reflect the paired experiment rather than treating related observations as unrelated samples.

5. **What can we claim if the effect is absent?** Only that this design did not establish a loss or recovery of the reported size and uncertainty on the tested distribution. We would publish the null, report failure modes and limits, and avoid an unstable recovery percentage.

## Current selected experiment and offline gate (2026-10-27)

Direction 1 is now selected. We are testing whether seemingly different findings in prior reports depend on **what their grammar actually permits**, using the same frozen cases and runtime. The original distractor-count proposal was not selected. Direction 2 (schema audit plus a selective higher-precision fallback) remains a possible follow-up, outside this pilot.

The four full-study arms mean: free generation; a loose grammar with an arbitrary-text escape; a strict call grammar activated by a trigger; and a strict grammar over the entire response. The loose arm can legally produce malformed calls through its escape. Triggered constraints can protect a call after its trigger without forcing the model to start a call. Whole-response constraints always require the chosen response language, including the explicit NO_CALL abstention sentinel. These are distinct interventions, not interchangeable versions of “JSON mode.”

Offline validation feeds strings into the real llama.cpp grammar parser without loading a model. All 6,194 recorded checks passed. That verifies the finite examples we tested; it does not tell us whether a model chooses the right tool, stops on time, or follows a trigger correctly at token level. We test those separately during serving. The scorer integration has six passing tests and uses the official BFCL AST matching logic. Official irrelevance scoring can accept an output containing no parsed call even when our stricter format check rejects its prose; both labels are retained.

Our frozen set has 60 simple, 60 multiple-tool, 60 parallel-call, and 20 irrelevance cases. The pilot uses a fixed subset of 50. Full-study arithmetic is three models × two precisions × four arms × five runs × 200 cases = 24,000 attempts. Five operational runs at temperature zero probe repeatability in this runtime; five seeds do not guarantee five statistically independent answers. We must preserve item pairing across all repeats rather than counting repeated copies as new benchmark items.

The pilot is 300 attempts: Qwen3-0.6B at F16, Q8_0 and Q4_K_M, with free and whole-response-strict decoding on the same 50 cases. The weights all start from one F16 export and caches stay F16. The pilot calibrates runtime/cost and reveals implementation problems. It is too small and has too few arms/runs to settle the full research question.

A cloud-credit payment of zero is not a zero-cost experiment. We count gross resource use against the $12 project cap, including failed setup, model preparation, image builds and storage. A $2.50 reservation is money held aside for a bounded batch, not evidence that $2.50 was spent. Measured seconds multiplied by account rates give a resource estimate; the billing report is a separate check and may arrive later. Other projects running on the same account make total account changes unsuitable for attributing this project's cost.

## Why setup failures remain in the budget

A pilot includes engineering checks as well as model answers. This session caught unsupported platform settings, a source file changed during image building, and a quantizer that could not launch in CPU-only preparation. Those are setup failures, not evidence that quantization damaged tool calling. They remain in the decision and cost logs. We corrected the quantizer command against the pinned source and build a CPU-only utility for preparation while keeping the CUDA server for inference. An interrupted local log stream is also recorded; it must not be turned into an invented model result. Source snapshots and a free-disk preflight protect subsequent runs.

## Earlier session’s outcome (before the successful retry)

Both selected Llama Instruct repositories now allow config and weight access. Qwen preparation succeeded, but the L4 worker never started during the bounded wait. Zero executed generations means accuracy and cost per generation are undefined, not zero. We have not learned whether quantization harms tool calling or whether constraints recover it. The setup costs are real and retained; a completed pilot is still needed before any full-run approval or budget forecast. See docs/PILOT_REPORT.md for the saved evidence. All Modal apps were stopped.

## Why the retry keeps one GPU for every comparison

The researcher approved L4 first and A10G as fallback. Modal calls that second request A10 and bills it using the A10G rate key. We record the actual device name rather than assuming which one was assigned. Different GPUs can change speed and numerical details, so switching hardware between free and constrained decoding could confuse the comparison. One worker now runs the entire 300-attempt pilot, including all three precisions and both arms; the scorer refuses to pool mixed GPU types or multiple worker sessions.

The launcher checks for active evalnoise apps and waits before launching, including when evalnoise is queued with no containers. It also monitors for new overlap and stops only this project’s app. The allowed 30-minute wait begins when our GPU request is submitted, after image building. Time waiting for scheduling is separate from GPU work; client wait can also include startup and network delay, so it is not used as a billed-GPU timer. The cost report uses the actual allocated GPU’s saved account rate. A forecast from A10 throughput describes A10 execution; it does not magically measure L4 speed.

## Successful retry: how to read these results

The 50 frozen questions produced six answers each: three precisions times two decoder settings, for 300 generations. All returned without operational errors on the same A10. This controls hardware across comparisons. It does not make the six answers independent benchmark questions.

Inference batches took 37.81 seconds total using four parallel slots. Dividing by 300 gives throughput averaged over concurrent work, not the latency of one user request. Reported successful-batch cost is $0.07962, about $0.000265 per generation. Charging all earlier setup/failures to this project gives $0.34336 so far. Those totals may still change as billing settles; the lower timer-based cost excludes building and other overhead.

The pilot scored 33/50 free and 35/50 strict at F16; Q8 matched those counts; Q4 scored 34/50 free and 36/50 strict. Q4 therefore was not worse than F16 in this small pilot. We cannot honestly compute a percentage of quantization damage recovered when the measured quantization loss is absent. The full four-arm/five-run experiment is still needed; one extra correct answer is not evidence that quantization improves models generally.

The forecast uses measured Qwen speed, but Llama speed and the two extra decoder arms remain assumptions. The $1 setup/storage allowance is a planning reserve, not an observed cost. A planning total under $12 does not prove every possible outcome will fit; measure and update before approving further batches. The full run is awaiting the researcher’s OK, and all apps are stopped.

## The full run is now approved

The researcher approved all three models on A10, preserving every arm and operational run. A failed collection is a separate engineering attempt. We retain its raw answers and cost, but repeat the whole interrupted model before forming the comparison frozen before execution. This decision was made without using its scores. It prevents an invisible mixture of collection sessions.

Each next model needs a fresh budget check. A forecast is our best estimate from earlier timings; a runtime deadline is a backstop if that estimate is wrong. Neither substitutes for the billing report. If the next model is projected to cross the project cap, the program stops and leaves the missing cells visibly incomplete.

The main confidence intervals resample both the original questions and the five operational-run labels, with the same draws for every condition. We also save intervals that resample questions alone. This shows how much the answer depends on observed run variation without pretending repeated copies are new questions. The intervals describe this frozen sample and runtime, not every local agent.

## Why a passed grammar test can still be followed by a serving error

The offline validator checks whether complete strings belong to a language. Lazy triggering has another boundary: a tokenizer can represent several characters as one token. In the aborted Llama setup, the model selected `[]` as one piece. The opening bracket activated the call grammar, but the remaining closing bracket violated its requirement for a nonempty call array. The server reported an error while replaying the already selected piece. A piece beginning `{'` caused the same kind of failure.

A positive runtime probe with a valid merged opener did not cover these invalid merged pieces. We therefore retain the exact engine errors as operational failures in the corrected full collection, without retrying them or weakening the grammar. Whole-response constraints and lazy constraints have different boundaries. An empty failed response is not evidence that the model forgot a particular argument value.

A separate setup error duplicated Llama's beginning-of-text marker. Its publisher template already supplied the marker, while the server also added one to string prompts. The corrected launcher passes the publisher token IDs directly, so there is one marker. The affected collection was kept as an aborted attempt before scoring its accuracy. Qwen's publisher settings add no such marker, and its completed data were unchanged.

<!-- generated-full-result -->

## What the completed full study means

Qwen/Qwen3-0.6B: Q4 required-call accuracy changes from 70.7% [64.0, 77.0] with free decoding to 75.6% [69.2, 81.4] with whole strict. Whole-strict incremental recovery is 2.1 percentage points [-0.7, 5.2]. Unstable denominator; no share CI. Q4 whole-strict parallel-call accuracy is 68.7% [57.0, 79.3]; a valid single call can still fail a task requiring several calls.

meta-llama/Llama-3.2-1B-Instruct: Q4 required-call accuracy changes from 14.2% [9.3, 19.4] with free decoding to 52.7% [45.3, 59.9] with whole strict. Whole-strict incremental recovery is -4.7 percentage points [-9.1, -0.3]. Undefined: nonpositive observed free loss. Q4 whole-strict parallel-call accuracy is 1.0% [0.0, 4.0]; a valid single call can still fail a task requiring several calls.

meta-llama/Llama-3.2-3B-Instruct: Q4 required-call accuracy changes from 29.2% [22.7, 35.9] with free decoding to 61.0% [53.9, 68.1] with whole strict. Whole-strict incremental recovery is -2.1 percentage points [-5.0, 0.6]. Undefined: nonpositive observed free loss. Q4 whole-strict parallel-call accuracy is 0.0% [0.0, 0.0]; a valid single call can still fail a task requiring several calls.

These compare the F16-to-Q4 accuracy gap with and without whole-response constraints. They subtract the benefit constraints already have at F16. Negative incremental recovery means the decoder helped F16 more, or harmed it less; it does not by itself mean constraints lowered Q4 accuracy. A confidence interval spanning zero does not establish the direction of recovery. Valid structure still does not guarantee a correct tool choice or value; the released diagnostics show both. Five repeated greedy schedules remain paired with their original questions, rather than being counted as new questions.


The later exclusion checks use saved answers only. Removing an incomplete answer from just one condition changes the comparison population. To preserve pairing, the matched check removes its corresponding answers from every condition of that model/item/run. A stricter check removes the entire item across runs too. These checks select on whether generation finished, so they can favor easier questions and cannot tell us what a longer generation would have answered. Full denominators and intervals are in results/full/full-002/FAILURE_SENSITIVITY.md.


meta-llama/Llama-3.2-1B-Instruct: on the same parallel questions, Q4 whole-strict accuracy changes from 1.0% under the original JSON contract to 62.3% [50.0, 74.3] under the Pythonic contract. This changes the serving contract as a whole, rather than isolating a parser-only effect.

meta-llama/Llama-3.2-3B-Instruct: on the same parallel questions, Q4 whole-strict accuracy changes from 0.0% under the original JSON contract to 88.3% [80.0, 95.7] under the Pythonic contract. This changes the serving contract as a whole, rather than isolating a parser-only effect.

Low parallel scores in the original JSON setup should not be treated as an intrinsic limitation of these Llama models. The separate report gives the matched protocol contrasts and their intervals. The original accuracy numbers and their precision interaction remain facts about the original contract.

<!-- /generated-full-result -->
