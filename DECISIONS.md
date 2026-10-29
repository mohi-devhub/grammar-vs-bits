# Decision log

## 2026-10-27 — Llama access confirmed; bounded pilot setup

After the researcher forwarded the access approval, authenticated config and actual weight-file HEAD requests returned HTTP 200 for **both selected Instruct repositories**, at their frozen revisions. Retrieved and hashed Meta's LICENSE.txt for each. Earlier 403 observations remain in docs/MODEL_ACCESS.json as history. No model substitution is needed; no token value was logged.

The first Modal attempt (pilot-001) was rejected during image definition because add_python requires the minor version 3.12, not 3.12.12. No preparation/inference function started. Stopped its app and retained the $2.50 reservation pending billing reconciliation rather than declaring zero cost. Corrected the SDK argument and reserved a separate $2.50 for pilot-002. Local Python is 3.12.12; Modal bootstraps the 3.12 series, so record the built image identity instead of claiming the same patch version. Both attempts count toward the cap until reconciled.

## 2026-10-27 — Freeze worker sources before launch

Pilot-002 built llama.cpp and installed/audited the hash-locked Linux dependencies (no known vulnerabilities), then Modal rejected a scoring.py change made during the build before the final source-copy layer. No model preparation or generation started. This avoidable source-freezing error is retained with its metered costs and stopped-app evidence. The launcher now creates a batch-specific source snapshot before importing cloud definitions; future local analysis edits cannot change that upload. Pilot-003 reserves another $2.50 (total conservative reservations $7.50) and reuses the cached build/audit layers. Runtime metadata now records the actual Python version.

## 2026-10-27 — Remove unsupported custom disk request

Pilot-003 copied the frozen worker source, then function registration rejected the 40-GiB ephemeral disk request: the platform minimum is 512 GiB. No worker started. Removed the custom disk request and use the documented default quota, retaining CPU/memory caps. Official source: https://modal.com/docs/guide/resources (checked 2026-10-27). App stopped, failure/cost evidence retained. Pilot-004 reserves $2.50, bringing conservative aggregate reservations to $10.00; no more reservation fits without reconciliation or user authorization. The built/audited image is reused.

## 2026-10-27 — CPU-only quantizer and local disk preflight

Pilot-004 downloaded weights and converted F16, but the CUDA-linked quantizer exited 127 in CPU-only preparation. Its loader stderr was lost when local disk exhaustion interrupted log streaming, so the exact missing library is not asserted. Add a static CPU-only quantizer built from the same pinned source, leaving GPU inference on the existing CUDA server. Capture local-file preparation subprocess diagnostics to the volume on failure. Freed only this repo compiler objects and venv bytecode; added a 256-MiB free-disk preflight. App stop was independently confirmed, with zero benchmark generations.

Revised the four stopped failed-attempt reservations to $0.50 each as conservative settling/storage allowances after inspecting tagged costs (under $0.10 to date). Retain original reservations/history, unknown missing bills and all failures; these allowances are not invented actual costs. Reserve $2.50 for pilot-005, for aggregate held funds of $4.50 within the unchanged $12 cap. No full run is approved.

## 2026-10-27 — Verify pinned quantizer CLI before retry

Stopped pilot-005 during initialization after source inspection showed nthreads is positional, not a --threads option. Corrected invocation to input output type 2; no model preparation or benchmark generation began. Retain a $0.50 settling allowance for this stopped attempt. Pilot-006 reserves $2.50; aggregate held funds $5.00. Source inspection also confirmed GPU server CLI flags; worker now emits saved server-log tails on failure. No model/precision/arm/run is changed.

## 2026-10-27 — Stop queued L4 pilot; no full-run approval request

Pilot-006 completed CPU conversion and quantization, recording source/output hashes and a 59.692075-second preparation timer before final cleanup/commit. Its L4 call then stayed queued for approximately fifteen minutes. At 14:06:50 UTC the function had backlog 1, zero runners and zero running inputs; cause not established. Explicitly stopped app at 14:07:42 UTC and verified all apps stopped, no containers, only main environment. Zero of 300 benchmark generations executed. Therefore accuracy, cost per generation and the full-run projection are unavailable; do not invent them or request full-run approval from this incomplete pilot.

Retained all setup failures, logs, tagged costs and conservative reservations. Added a noninteractive --yes shutdown, automatic queue-wait watchdog, saved-artifact reuse flag and per-batch model metadata for the next pilot attempt. These new launcher paths have only local verification, not a new paid run. Prepared models remain on the budgeted volume. No question/grid change, no full run, no November execution, no replacement GPU.

## 2026-10-27 — Authorized serialized retry with ordered GPU fallback

Researcher explicitly requested retry: ordered L4 then A10G fallback, 30-minute total queue wait, no overlap with any active evalnoise app, same GPU type for every arm within a run, no full-run launch. Modal documents the canonical request string A10; the authenticated rate key is gpu_hour_cost_a10g. Use gpu=["L4","A10"] in one worker invocation for all 300 attempts; detect actual hardware using nvidia-smi and attach it to every row. Compile both native SM86 and SM89 kernels from the same pinned source; prior SM89-only binary cannot safely serve A10. No model, case, arm, seed or quantization change.

Reserve $2.50 for pilot-007, bringing conservative held funds to $7.50 within the $12 October cap. Current rates L4 $0.80/hour and A10G $1.10/hour; with two cores and 16 GiB host memory, ceiling rates are $1.0226/$1.3226 per worker-hour. This reservation includes rebuild, bounded execution and storage; it is not actual spending. Evalnoise apps were stopped at initial check. The launcher waits before launch and before enqueue, and stops only our app if a background check detects new evalnoise activity. An interlock interruption must be logged and retried only after evalnoise finishes; never kill its app. Official fallback behavior: https://modal.com/docs/guide/gpu#gpu-fallbacks.

## 2026-10-27 — Detached retry with cloud-side deadline and durable event relay

Pilot-007 waited until evalnoise stopped, then its app was stopped externally during the CUDA build. Lifecycle has no stopping actor; heartbeat/client-disconnect messages do not establish a deliberate user stop. No GPU request or generation occurred. Retain the failure/logs and costs.

For pilot-008 use detached app mode plus a bounded CPU supervisor that enforces the 1,800-second GPU-start limit and evalnoise interlock in the cloud, checkpoints every streamed event to the project volume, and self-stops only its own app. Local controls remain as backup. Supervisor hard limits are 0.25 physical cores/1 GiB RAM; its queue-time CPU cost is separate from unbilled GPU scheduling and included in the batch allowance. No automatic GPU retry or cross-device pooling is introduced.

Reuse exact audited image im-9fka2nV2OfiyVZP8chYC1i and its compiled CPU code; rebuild only the CUDA target for SM86 native. NVIDIA explicitly documents that an 8.6 cubin can execute on an 8.9 GPU (https://docs.nvidia.com/cuda/ada-compatibility-guide/index.html), allowing both A10 and L4 without compiling duplicate architecture variants. This serving build policy is recorded and must be held fixed for comparisons. Keep an explicit from-source reproduction branch. No quantized model artifacts are changed. Reserve $2.50 for pilot-008 (aggregate conservative holds $10.00 under the $12 cap).

## 2026-10-27 — Pilot completed on A10; full run remains gated

Pilot-008 completed 300/300 fixed generations with ok status on one NVIDIA A10; all three precisions and both arms used that device. The ordered fallback selected A10, with an 18.458-second client wait including scheduling/startup/RPC. The server confirmed the intended GGUF types and returned timing cache_n=0 throughout. GPU body 44.850405 seconds; inference batches 37.814643 seconds. Actual Linux audit: 104 dependencies and no reported vulnerabilities. Cloud supervisor durably checkpointed events and stopped its own app. Final app list stopped, containers empty. Nine local tests pass.

Reported tagged costs at 2026-10-27T17:11:06.202272+00:00: retry $0.07961645, project $0.34335856; metering may lag and storage completeness is not established. Revised remaining reservations for stopped/completed attempts to $0.50 each ($4 total), keeping original holds/history and all failure logs. Full forecast assumptions and costs are generated in results/pilot/pilot-008/budget_forecast.json; they are not measured Llama throughput. Planning can fit October, but the stress case is close to $12; refine before committing the full matrix and propose a month split if required. No full run or November execution occurred.

Pilot scores show no positive Q4 free precision loss; recovered-share percentage is undefined. Do not describe that point estimate as proof of equivalence or resolution of the four-arm question. Direction 2 stays the planned follow-up.

## 2026-10-27 — Direction 1 selected; October cap revised to $12

The researcher explicitly approved the Direction 1 anchor models (Qwen3-0.6B, Llama-3.2-1B-Instruct, Llama-3.2-3B-Instruct), FP16/Q4_K_M, 200 frozen BFCL cases, four arms, and five operational runs. Direction 2 is the planned follow-up. The full 24,000-generation run remains unapproved until the measured pilot report. October cap is $12 gross project resource cost, including failed work/preparation/storage, sharing user-reported ~$28 with noise-check's separate $12 cap. A possible November split is a proposal only, not permission to spend November credits.

The unchanged pilot shape is 50 cases × FP16/Q8_0/Q4_K_M × free/whole-response-strict = 300 attempts, on Qwen3-0.6B from the now-selected anchor grid. Q8_0 is pilot-only, not an extra full-run precision. Five operational runs and all four main arms must not be reduced to force a budget fit.

Initial authenticated HEAD checks: Qwen3-0.6B config and weights accessible; both official gated Llama repositories returned 403. Later checks after approval returned 200, as recorded above. The researcher supplied Modal secret `huggingface` with key HF_TOKEN, authorized its use only in downloading functions, and instructed continuing offline validation and the Qwen pilot while approval is pending. No credential value is printed or stored. Recheck official Llama access once approval arrives; if pending tomorrow, propose an ungated substitute without silently changing models.

Local disk exhaustion prevented installing/downloading PyTorch weights locally. Removed only this task's redundant source archives and unused older checkout; left other project files/caches alone. Keep the repository uv environment for orchestration/scoring, with Torch conditional on Linux; prepare/convert public Qwen weights in a bounded CPU Modal job. This changes execution location, not the research design. Record all image/preparation costs.

Runtime source is official llama.cpp commit 8542e94350f0ade01644db6f1d1520da3814dafd. Followed the official BFCL site's current source to ShishirPatil/gorilla commit 6ea57973c7a6097fd7c5915698c54c17c5b1b6c8; the earlier gorilla-llm checkout was not used for data/checking and was removed. Archive hashes are recorded. The pinned unmodified AST checker is imported with only a lightweight registry entry (underscore_to_dot=False), avoiding unrelated provider SDK imports. The unchanged official irrelevance helper uses our parsing adapter; format/finish diagnostics remain separate.

No inference-dependent data selection: froze 60 simple_python, 60 multiple, 60 parallel, 20 irrelevance, using seed 20261027. Pilot is a fixed 15/15/15/5 subset. Raw source rows/references and hashes remain unchanged. Grammar normalization translates BFCL dict/float types to JSON types, closes documented property sets, and treats optional as metadata with the source required list authoritative. In parallel_29 a nested dict lists required names without property types: compiler retains those names with unconstrained values, never guessed gold-value types. Document this schema-only policy.

Offline membership validation passed 6,194 cases against the real pinned llama.cpp parser, both model families. This is finite character-level evidence, not proof of all schema coverage or token-level runtime enforcement. The upstream validator exits zero even for rejected strings, so the harness checks its explicit membership message. Six official-scoring integration tests passed. Local pip-audit is clean; remote image must also pass its audit before a GPU pilot starts.

## 2026-10-27 — Continue gap analysis; no direction approved

The researcher explicitly requested a deeper audit of eleven overlapping works and ranked alternatives in docs/DIRECTIONS.md, with no cloud spend and no approval of the earlier distractor-count proposal. The project remains active in design. The new document proposes four alternatives and recommends a controlled strict-versus-permissive replication; it also specifies a schema-audit/precision-fallback solution candidate. Every model/grid amendment remains a proposal. Neither a recommendation nor the future direction choice waives the original pilot/full-run approval gate.

The deeper audit preserves prior strengths: QuantCall's weight sweep includes paired-delta inference; Repair, Not Improvement uses five server seeds and paired intervals; Wu includes build/rounding repeats on subsets. Gaps are attributed to specific experiments, not entire projects. Cost estimates use current official Modal prices and explicitly unmeasured runtime envelopes; they are not measured costs or permission to launch.

## 2026-10-27 — Step 0 precedes implementation

The repository was empty and no applicable AGENTS.md was found in the directory ancestry. Perform the requested literature check before installing dependencies, downloading models, building llama.cpp, or launching Modal compute. Inspect third-party repositories as text only. Create no experimental results or manuscript claims without measurements.

## 2026-10-27 — Novelty hold, question unchanged

Read Flat Score (2607.27275v1) and BF16 or Death (2411.02355v4), and search connected prior literature/software. QuantCall, QuantMCP, Toolhound, and small-model structured-generation papers directly overlap the proposed explanatory headline. The exact requested full-schema experiment matrix was not verified as already answered. Hold implementation because the broad contribution needs a more precise distinction; this is a judgement about novelty risk, not an assertion of an exact duplicate. Detailed evidence is in docs/RELATED_WORK.md and docs/NOVELTY_CHECK.md.

Propose precision × distractor-tool-list-length under both decoding conditions as the main question, or a carefully narrowed cache-only alternative. Both remain unapproved. The user explicitly required asking before changing the research question; do not implement a pivot until they choose. This hold does not imply that the user has approved a reduced model/precision grid or a new pilot.

## 2026-10-27 — Recovery needs a matched FP16 control

Keep a constrained FP16 arm. Subtract the FP16 constraint effect when estimating quantization-loss recovery. Full schemas constrain tool names, argument names, and types, so recovered accuracy is not automatically a pure syntactic share. Record the original proposed headline as unresolved rather than silently redefining syntax or changing the research question. See docs/PROTOCOL_NOTES.md.

## 2026-10-27 — Provenance and access

Use primary citations, pinned GitHub evidence, and explicit review scopes. GitHub's unauthenticated API was rate-limited; use read-only git ls-remote for repository revisions. Unverified aggregator-only leads are excluded. No downloaded source was executed. Official model pages show Apache-2.0 for Qwen 1.5B, Qwen Research for Qwen 3B, and gated Llama 3.2 terms for Meta 3B. Authenticated weight access and artifact hashes remain pending.

## Standing budget, security, and run gates

- Current October project cap: $12, including preparation, builds, inference, storage, retries, and idle compute attributable to this project (supersedes the initial $15 cap).
- Before a batch: record projected cost and remaining budget. If projected over $5, ask before launch. Never run a batch that would breach the project cap without new authorization.
- Pilot: one model × FP16/Q8_0/Q4_K_M × 50 items × free/constrained; report measured costs and timing. Wait for the user's explicit OK before the full run.
- Install only pinned official-source packages in this repository's uv environment, maintain hashes, and run pip-audit before compute. No installation has occurred at the novelty stage.
- Keep credentials out of outputs and commits; .env and local caches are ignored. Model preparation must not execute unreviewed remote model code.
- Keep containers warm only during active work; stop project apps after each compute session and check Modal status. Read-only session evidence is logged in BUDGET.md.
- Generate manuscript metrics and figures from real results through scripts, including null or negative findings. No placeholders may be reported as measurements.

## 2026-10-28 — Full matrix approved, A10 only

User explicitly approved launch of all three models, F16/Q4_K_M, four arms, five operational runs and the same frozen 200 cases. New execution constraints: A10 only; no A10 within 30 minutes means stop/report; check spending after every model and refuse a next model projected to breach the $12 total; finish before October 31. Keep evalnoise serialization. Full run uses the exact pilot runtime image and pin. Implement paired item-cluster bootstrap CIs and preserve every raw response/status. Runtime lazy-trigger probes are synthetic setup, separate from benchmark attempts; use numeric trigger type 1 (word) per the pinned server schema, including both object/array starts for Llama parallel calls. Freeze native template date to 27 Oct 2026 so day changes cannot change prompts. No research-question change.

## 2026-10-28 — Trigger transport verified against pinned source before launch

The native /completion endpoint accepts numeric grammar trigger type 1 (word), but common_sampling_add_grammar_triggers requires any single-token word to appear in preserved_tokens first. Added preserved_tokens for Qwen <tool_call> and both Llama JSON object/array starts in main requests and synthetic probes. The pinned grammar accept implementation explicitly replays the trigger token/text against root, so the grammar includes its native prefix. Tests cover these transport details. This was corrected while waiting for evalnoise, before any new cloud model session or benchmark output. No question/schema/case change.

## 2026-10-28 — Token-boundary-independent Llama trigger

Before any model session started, refined Llama trigger transport to numeric type 2 pattern (\[|\{), matching the earliest array/object opener even when a token contains a merged prefix such as {". A type-1 word opener can be converted into one exact token and fail to activate on merged pieces. Qwen retains its preserved native <tool_call> word/token trigger. Synthetic probes bias the first token of each complete target, so Llama probes exercise the actual merged-token replay where present. The pinned llama_grammar_accept_impl replays overlapping token pieces from the match. No benchmark prompt, schema, item, reference or outcome was used for this fix.

## 2026-10-28 — Analysis tooling and interval contract

Added local-only analysis dependency Matplotlib 3.11.2 from official PyPI in an analysis group with hash export; local analysis audit is clean. The GPU runtime is unchanged. Pinned TinyTeX-1 v2026.10 from rstudio/tinytex-releases for repository-local paper compilation, verified its official asset digest and disabled ad-hoc package downloading.

The selected DIRECTIONS.md specifies crossed paired resampling of original items and operational runs. Primary CIs therefore resample item IDs and five run labels with shared draws across all conditions/models. Item-only CIs are also saved as a sensitivity check to satisfy the original item-resampling request. Neither treats five duplicate greedy outputs as five independent items. Tests cover identical-repeat invariance, paired constant shifts and shared run variation. Qwen live trigger preflight passed on A10 before benchmark generation.

## 2026-10-28 — Interrupted first Qwen collection retained; whole-model restart

The first full controller waited for evalnoise, then Qwen runtime probes passed on A10. The app was cancelled with 2,936 durable generations, all status ok, but only 2,088 reached local streaming. Recovered the cloud log, retaining both versions. No Llama model launched. Cleanup overwrote the first shutdown reason; the exact trigger is not established. The post-model billing request also failed transiently. Retain the $0.15594981 reported cost and a $0.50 settling hold; do not call a conservative envelope a measured GPU-body cost.

Full-002 restarts Qwen completely, before any scores from the interrupted model were used. Full-001 remains an aborted operational attempt and is excluded from the primary complete matrix, with raw outputs and cost retained. Added first-cause/history retention, redacted status-error diagnostics, three bounded status-check failures before interlock shutdown, and bounded retries for uncharged billing reads. A positive evalnoise check still stops only our app immediately. No prompts, data, decoding languages or A10 inference parameters changed. All stopped-app and empty-container evidence is retained.


## 2026-10-28 — Qwen completion recovered; laptop-independent submission

Full-002 Qwen completed all 8,000 requests on one A10. Normal self-shutdown cut off the large client stream at 7,763, but the durable checkpoint contains the complete unique matrix, ten blocks and the GPU completion event. Preserve the truncated stream and its exit code, adopt the validated checkpoint without rerunning inference, and reconcile its $0.39501664 reported app cost. Updated local recovery verifies coverage/provenance before accepting a cloud checkpoint.

The first Llama-1B launch failed during control-plane connection before any GPU request or model artifacts. App and container evidence confirms shutdown, logs are empty and no Llama model directory exists. The macOS power log records sleep during the launch. Retain the failed setup attempt and a $0.50 settling allowance, not a claimed measured charge. New submission performs CPU preparation and GPU submission inside one detached cloud entrypoint. The local client waits for cloud shutdown and recovers a completed checkpoint after delivery interruption. No inference, prompt, schema, data, arm or run setting changed.


## 2026-10-28 — Evalnoise restarted during preparation

A new evalnoise-study app started during the Llama-1B CPU preparation. Preparation completed and its official-weight artifacts/hashes are retained, but our app was stopped before benchmark generations (zero). Retain its $0.00855848 reported cost and $0.50 settling hold. Never stop the other project. Add a post-preparation active-app check before GPU submission, backed by a test that even a queued evalnoise app prevents GPU invocation. The local full controller now requires a 180-second quiet interval before opening a paid session, reducing launch races between another project's batches. The cloud watchdog still stops only our app if overlap begins after launch. Dataset, prompts, decoding languages, seeds, inference engine and GPU type remain unchanged.


## 2026-10-28 — Correct native Llama BOS; retain lazy-trigger failures

The first Llama-1B block completed 800 attempts: 792 ok, six token limits, two HTTP 500 errors. Server logs show duplicate BOS tokens. Pinned server source adds BOS for string prompts; the rendered Llama template already contains it. The tokenizer audit across all 200 prompts shows one additional BOS for each selected Llama and no addition for Qwen. Qwen's publisher config explicitly disables added BOS, which the pinned converter writes to GGUF. Retain this Llama collection as an aborted technical attempt before scoring its task accuracy. Future Llama requests use the pinned server's integer-token prompt transport with exactly one native BOS. Qwen's existing string transport/data are unchanged.

The two trigger-strict HTTP 500 responses report empty grammar stacks accepting merged pieces `[]` and `{'`. Lazy activation samples the trigger-containing piece before full grammar masking; an invalid remainder can fail replay. These are observable intervention failures, not permission to admit invalid text. Classify that exact trigger/HTTP/message combination separately and count it as incorrect without retrying. Continue the registered matrix for this known per-item error. Unknown request/configuration errors still stop the worker. Publish operational rates/CIs alongside task and schema rates. No grammar, prompt text, accepted answer, item, arm, precision or seed was changed.


## 2026-10-28 — Spawned-job durability verified before further GPU work

The first corrected Llama collection was cancelled at 3,592 locally received attempts (21 token limits; remaining responses ok). No worker error or evalnoise stop was recorded; cancellation arrived while the laptop was asleep. The outer entrypoint still used a synchronous remote generator. Retain the incomplete attempt and $0.24810816 reported app cost, before task scoring.

Replace only the laptop-to-cloud invocation with a non-generator Function.spawn job. The cloud consumes and checkpoints GPU events internally; the client retrieves and validates the complete checkpoint after shutdown. The official [Modal invocation guide](https://modal.com/docs/guide/function-invocation-methods) distinguishes asynchronous spawn handles from synchronous remote generators. A bounded CPU-only probe intentionally exited its local launcher immediately after spawn, then completed its 35-second cloud body and self-stopped. Its durable completion file is saved in results/ops/detach-probe-001_completion.json. Reserve $0.05 for this infrastructure test; not a measured cost. The same queue, interlock and budget watchdogs remain in the cloud. Inference code, native prompt transport, conditions, cases and run seeds are unchanged.


## 2026-10-28 — Spawned model interrupted by required cross-project interlock

The first spawned Llama run produced 2,811 durable observations, including 15 token limits, before evalnoise launched another app. The first shutdown reason explicitly records the evalnoise interlock. The partial data are retained; the initial local stream count of zero is not the executed count. No task scores were used to exclude the entire interrupted model. The other project subsequently launched a durable remaining-study job, confirmed through its status/ledger read-only. Do not modify or stop that project. Wait for its active study to finish before another paid launch; retain the quiet interval and in-cloud guard. Reconcile stopped-attempt holds against fresh attributed billing while keeping a settling allowance; this does not invent actual charges or change the $12 project cap.


## 2026-10-28 — Count durable aborted observations rather than client delivery

A local inventory parsed each retained aborted checkpoint without scoring accuracy. The first corrected Llama attempt has 4,339 durable observations, compared with 3,592 delivered locally. Its original client count is preserved. The other nonempty aborted Llama checkpoints contain 800 (duplicate-BOS setup) and 2,811 (evalnoise interlock) observations. Copies of one checkpoint are not pooled as extra attempts. Primary analysis still uses only the complete, correctly configured registered model matrices. Full checkpoint-by-checkpoint counts are in results/ops/full-002_aborted_observation_inventory.json.


## 2026-10-28 — Separate observed cancellation from its unconfirmed cause

For full-002-2-native1, cancellation and an incomplete checkpoint are observed; the precise stopping actor/cause is not established. Laptop sleep and a client-bound generator were operational concerns, not proof that sleep caused that cancellation. The source-state description now says so. Spawn durability was independently verified by the CPU probe. For the later spawn1 attempt, the first-cause file specifically establishes the evalnoise interlock. Do not conflate these two stopping events or attribute either to model semantic degradation.

## 2026-10-28 — Keep one state writer and publish complete JSON snapshots

While no project cloud app was running, reloaded the local waiting controller after auditing aborted checkpoint counts. This ensures it owns the latest corrected history rather than later overwriting it with an older in-memory copy. The local finalizer was also reloaded. Metadata JSON writes now replace complete same-directory temporary files atomically, so the finalizer cannot read a half-written state snapshot. Runtime prompts, seeds, schemas and decoding parameters are unchanged.


## 2026-10-28 — User approved concurrent full studies

The researcher explicitly answered “Allow concurrent full studies” to the scheduling-scope clarification. Full-study apps from evalnoise may now coexist with this approved full run; pilot and unknown noise work remain blocked. One shared predicate applies the scope consistently in local launch checks and the cloud watchdog. Separate $12 project caps, A10-only allocation, the 30-minute queue cutoff, model-level cost gates, all cases/arms/runs and self-shutdown are unchanged. Cross-project timing context is recorded; do not claim isolated cross-model throughput. No research question changed.


## 2026-10-28 — Complete registered matrix and retain negative results

All primary model sessions completed on A10 with every original case, precision, decoder arm and operational run. Integrity checks found no missing or duplicate primary observations. Interrupted attempts remain separate. The required-call endpoint, official checker and paired analysis are unchanged. Results retain token-limit outcomes, the lazy-replay failure, signed negative interactions and unstable or undefined recovery shares. Category scores were already specified; reporting parallel versus simple accuracy helps explain the aggregate without changing its denominator. Direction 2 remains planned and unevaluated.

The manuscript is built from saved results using the pinned local TeX distribution. Its optional microtype package was unavailable and removed; no measurement changed. Final tests and dependency-audit evidence, PDF review, archive hashes and shutdown evidence are linked in results/full/full-002/verification.json. The cloud archive preserves raw outputs and manifests before removing regenerable GGUF caches. Other authorized projects are left running. Packaging creates a local artifact and does not publish it.


## 2026-10-29 — Requested post-hoc operational-failure sensitivity

No model inference or cloud work is authorized for this check. Keep the registered analysis counting failures as incorrect. Before estimating exclusion effects, specify three supplementary analyses: remove only token-limit/replay observations within each cell; remove an item/run panel from all eight conditions of its model if any condition failed; and remove an original item from all conditions and all five runs if any failed. The first conditions on different completed populations, while the latter two retain common comparisons but select on post-treatment outcomes. Use crossed paired item/run bootstrap draws, retain every reported sensitivity and its denominator, and disclose any sign or interval interpretation changes without replacing the primary endpoint.


## 2026-10-29 — Exclusion checks complete; preserve registered inference

The raw and scored failure inventories agree. All token-limit responses reached the saved output cap; the single replay failure is retained with its exact raw server error. Cell-only, matched-panel and complete-item exclusions are all reported, with their changed denominators. No recovery-effect direction or zero-inclusion interpretation changes across these checks, and paired decoder-contrast interval interpretations also remain unchanged. A boundary within floating-point round-off of zero is treated as zero rather than as a newly directional result. The manuscript limitations now disclose condition-dependent failures and post-treatment selection. Primary raw outputs, official scores and summary hashes remain unchanged. Only local analysis, tests, manuscript build and release packaging ran; no cloud jobs or new model generations were launched.

## 2026-10-29 — Apply audit and freeze optional Pythonic sensitivity

User authorized every High/Medium audit fix, L1 qualification, public repository mohi-devhub/grammar-vs-bits, MIT first-party code, upstream Apache-2.0 notices, and an optional additional $3 A10 sensitivity. The primary prompts/results remain unchanged. The new sensitivity freezes the original60 parallel items and60 deterministically sampled parallel_multiple items, both Llama models, F16/Q4, free/whole strict and all five operational run labels. Meta call-list syntax is used with paraphrased instructions and [] for no call. It changes the joint prompt/parser/grammar contract; it cannot isolate syntax from meaning. All811 finite C++ grammar checks pass after supporting both quote forms on nested dictionary keys. The guard still blocks unknown/pilot evalnoise work. No source-faithful replication of prior studies is claimed.

## 2026-10-29 — Recognize the verified evalnoise full-cohort follow-up

Read the other project's experiments/l4-followup.json without modifying it: it is approved, uses500 frozen items, four models, both arms and12,000 planned outputs on L4. It is a full-cohort follow-up, not a pilot. The existing user permission for concurrent full studies therefore applies. Add only its exact app description, evalnoise-l4-followup, to that classification; unknown noise work and all pilots still block. Restart our local waiting controller before any cloud submission so it uses the clarified guard. No other project app is stopped or modified.

## 2026-10-29 — Retain a zero-generation optional setup failure

pythonic-001-1 failed while importing full_cloud in the new cloud module, before any benchmark events or GPU worker submission. Stopped only ap-7NzFvlnymH2f0t1G8mWAgf; initial reported charge $0.00005412 remains included. Retain a $0.10 settling hold, not an alleged final cost. Explicitly package the imported module in the optional image. The data, grammar, prompts and five run labels remain frozen; use a new attempt ID pythonic-002. Tighten each new model envelope to $1.35 (calculated resource ceiling $1.30903) so both plus the failed-startup hold and storage buffer remain below the unchanged $3 additional cap.

## 2026-10-29 — Retain a platform interruption and continue only missing sensitivity cells

Modal reported “Input aborted due to internal failure (e.g. preemption)” in the Llama-3B Pythonic worker. The precise platform cause is unconfirmed. The supervisor and GPU raw checkpoints contain the same 1,610 unique generations. All are retained, including failed responses. No recorded response is regenerated based on its accuracy or status. The missing 790 keys are determined solely by checkpoint coverage and continue on another A10 with the same prompts, grammars, sampling settings and quantized artifacts. Previously completed precision blocks are skipped; the original shuffled schedules are filtered by recorded keys. In-flight work without a durable output cannot be scored and may already have incurred cost.

Before continuing, verified prior apps stopped. A bound using each closed app's entire lifetime plus startup allowance, conservatively charging GPU, preparation and supervisor resources simultaneously, plus a new $1.35 envelope and storage buffer, is $2.6498525 within the approved additional $3. Project reservation and reported-cost gates also remain below $12. The continuation is spawned detached, retains its own source hash record, app ID, raw outputs and billing. The original interruption state is preserved. This is a disclosed worker restart within a separate sensitivity analysis, not a replacement primary session or a change in the research question.

## 2026-10-29 — Rename and reframe the public release

The user requested the canonical name Grammar vs Bits and release v0.1.1. Renamed the existing GitHub repository with gh repo rename, preserving Git history/releases and the former URL redirect, and updated the local remote and maintained publication links. Distribution metadata and new app names/tags use the canonical name. Retain the qunti import namespace, immutable worker snapshots/raw records, existing volume addresses and historical billing selectors for reproducibility. No models are run and no primary numbers are changed.

The abstract, introduction, conclusion and README now lead with the separate matched-parallel format sensitivity. Compare its observed Q4 contract gains with F16-to-Q4 point gaps on the same Pythonic parallel endpoint, rather than comparing different item cohorts. This is a joint prompt/parser/grammar comparison across different sessions, not a randomized parser-only causal effect or a general law that precision never matters. Sensitivity incremental recovery remains inconclusive. The paper's per-model/precision/arm table exposes all sensitivity token limits, which already count as incorrect; no unlimited-generation or new exclusion result is claimed. Direction 2 remains planned and unevaluated.

## 2026-10-29 — Apply the editing audit and publish v0.1.2

The user approved release v0.1.2 with the method overview, readability edits and AUDIT-edits.md wording fixes. Use the exact requested primary JSON-contract point-estimate qualification in both openings, describe the separate format comparison without causal verbs, and restore the throughput caveat. Shorten related-work and limitations prose to retain six pages without changing type sizes, margins, float spacing, figures, scientific numbers or results. Preserve historical audits and the original editing change list; record the final fixes in docs/AUDIT_EDITS_RESOLUTION.md and include those records in the archive.

Bump only the project's distribution version and citation metadata; dependency versions and hashes remain pinned. Rebuild locally, run existing tests, pip-audit, provenance and checksum checks, verify the former repository redirect, and publish the reviewed commit and assets. No model inference or cloud compute is authorized or needed for this release. Direction 2 remains planned and unevaluated.

## 2026-10-29 — Release v0.1.3 with float placement and keywords only

The user authorizes a layout-only update, keywords after the abstract, a rebuilt arXiv ZIP and public release v0.1.3. Allow up to seven pages rather than compressing content. Add the official, hash-pinned CTAN placeins package and float barriers before the limitations and bibliography, so result floats finish before References. Preserve every scientific sentence, numeric input, figure asset, saved result and executed snapshot. Include the reproducible arXiv packager; keep unrelated local professor-briefing files outside the release inventory by packaging tracked files only. No model inference or cloud compute is needed.
