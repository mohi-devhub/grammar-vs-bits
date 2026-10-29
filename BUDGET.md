# Project budget — selected Direction 1

Updated 2026-10-28. Gross metered resource costs count even when credits make the cash invoice zero. The dated sections below preserve earlier decisions. The current authorization is the final full-run section.

**October project cap: $12.00**, superseding $15. User-reported shared remaining October credits are approximately $28; noise-check has its own $12 cap. Keep the noise-check reserve separate. No November execution is approved. The researcher approved the full run after the pilot report on 2026-10-28.

## Authorized workload

Offline grammar validation, pinned setup and the pilot are authorized. The pilot is Qwen3-0.6B × F16/Q8_0/Q4_K_M × 50 fixed cases × free/whole-strict = **300 benchmark attempts**. Three single-token warmups are separate setup, not extra benchmark data. Full design is three anchors × two precisions × four arms × five operational runs × 200 cases = **24,000 attempts**. No arm/run reduction is authorized.

## Rates and bounded reservation

The authenticated `modal billing rates --json` response is saved in results/ops/rates.json (2026-10-27): L4 **$0.80/GPU-hour**, CPU **$0.04730/physical-core-hour**, RAM **$0.008/GiB-hour**, volume storage **$0.09/GiB-month**. These precise account rates slightly differ from rounded public per-second planning figures in DIRECTIONS.md.

One GPU worker, capped at two physical cores and 16 GiB host memory: **$1.0226/hour**. CPU-only preparation at the same CPU/RAM caps: **$0.2226/hour**. Both use one container, no automatic retries, and the shortest supported idle window (2 seconds), followed by explicit app shutdown.

Reserve **$2.50 for each explicit pilot attempt**, before any cloud call, covering image builds, CPU model preparation, bounded L4 startup/pilot, and storage allowance. This is a conservative reservation, not measured spending or a guaranteed invoice ceiling. CPU preparation timeout is 1,800 seconds. GPU function timeout is 1,500 seconds, startup timeout 900 seconds, and its internal generation deadline is 1,100 seconds. CUDA CMake configure/build subprocesses have 300/900-second timeouts; the added CPU-only utility has 180/300-second configure/build timeouts. Build resource allocation is platform-controlled and will be reconciled from billing. Avoid retrying a failed build or invocation without retaining its cost/reservation.

The reservation is below the $5 per-batch approval threshold. The launch script atomically reserves it and refuses duplicate pilot launches or aggregate reservations above $12. No full-run launcher exists in the pilot code. Each subsequent batch must be projected and reserved before launch; ask before a batch projected over $5.

## Ledger and attribution

| Stage | Projected/reserved USD | Actual metered project cost | State |
| --- | ---: | --- | --- |
| Source review, local setup and grammar/scoring tests | 0 cloud spend | 0 cloud workload launched | Complete |
| pilot-001: image-definition rejection before worker startup | 0.50 revised settling allowance | Pending billing reconciliation; absence of a row is not proof of zero | App stopped; failure recorded |
| pilot-002: built/audited image; source-copy rejection | 0.50 revised settling allowance | $0.08513749 reported to date; not settled | App stopped, no generation |
| pilot-003: disk-request registration rejection | 0.50 revised settling allowance | Pending billing reconciliation | Stopped; no preparation/generation |
| pilot-004: CPU conversion completed, quantizer startup failed | 0.50 revised settling allowance | Pending tagged reconciliation | Stopped; zero benchmark generations |
| pilot-005: cancelled in initialization to fix CLI | 0.50 settling allowance | Pending | Stopped; no worker |
| pilot-006: model preparation succeeded, L4 queue stopped | 2.50 retained reservation | $0.02138465 reported to date; not final | Stopped; zero benchmark generations |
| Full 24,000-attempt experiment | Must use pilot measurements | Not run | Wait for post-pilot OK |
| November continuation | Not yet estimated | Not run | Proposal only if needed |

Machine-readable reservations: results/budget_ledger.json. The four stopped failed attempts originally reserved $10.00. After shutdown and tagged billing review, retain $0.50 per attempt ($2.00 total) as a conservative settling/storage allowance; this allowance is not actual spending. Pilot-005 was cancelled in initialization and retains a $0.50 settling allowance. Reserve another $2.50 for pilot-006 ($5.00 total held across six explicit attempts). This is not measured spending. The shared-account baseline is results/ops/billing_before.json; other project work is concurrent, so account-level before/after differences are **not** this project's actual cost. New apps use `project=grammar-vs-bits`; the historical pilot used `project=qunti-check, stage=pilot` and save tagged billing reports. Retain actual resource timings separately from invoiced/metered cost and note reporting lag. Never report $0 cost because credits offset the invoice.

The noise-check ledger was read solely to understand shared constraints; it was not modified. Its reservations are not measured charges and are not available to this project. If authoritative remaining shared credits cannot cover its outstanding reserve plus this project's next batch, stop before launch.

## Reporting and possible month split

Report inference-only and all-in timing/rate-based cost per generated response and per unique item, with denominators stated, plus settled project-tagged metered cost when available. Function/client wall time is not a precise measure of billed GPU occupancy: startup, image builds, loading, warmup and idle must be identified.

Project every unchanged full-run cell using measured timings; label unmeasured model/arm extrapolations as assumptions and uncertainty. Preserve failed attempts and all five runs. If the full run will not fit the remaining October project/shared budget, propose specific complete cells for October and the rest from November 1, retaining all cells/runs and the same frozen data/runtime. **Wait for approval before either part of the full run.**

## Shutdown

No project Modal app was launched during offline validation. After each cloud session, stop the project app in a finally block, save app-list evidence and explicitly report any other active app. Do not attribute another project's compute to this one. Historical shutdown evidence is in docs/MODAL_STATUS.json; current pilot shutdown is recorded in results/ops/BATCH_shutdown.json when a session finishes. Pilot-004 needed an independent shutdown recheck after local disk exhaustion interrupted final evidence writes.

## End of session — incomplete pilot

[Status report](docs/PILOT_REPORT.md): model preparation succeeded; L4 request remained queued for roughly fifteen minutes with zero runners at the final check. Stopped the app. Executed generations: 0/300. Measured cost per generation and full-run projection are **unavailable**, not zero. Gross tagged project costs reported to date are **$0.10997947** at 2026-10-27T14:09:07.645587+00:00, including setup failures; billing/storage completeness remains unresolved. Retain $5.00 in conservative reservations; no further batch was launched. All listed apps are stopped and container list is empty; environment list contains only main. Final evidence is in results/ops/session_final_*.json.

Prepared GGUF files remain on the project volume for reuse. Persistent storage continues to count against the budget; the reservation includes a storage allowance. No November compute is authorized. Do not propose a measured October/November allocation until a completed pilot supplies throughput.

## Authorized retry — pilot-007

User approved ordered L4/A10G fallback and 30-minute queue wait, serialized with evalnoise. Reserve $2.50 before launch (aggregate reservations $7.50). Use saved Qwen artifacts; all 300 attempts share one GPU worker/type. Actual allocated device is recorded per item. Current authenticated rates are in results/ops/rates-retry.json: A10G $1.10/GPU-hour, giving $1.3226/worker-hour at the existing CPU/RAM caps. The 1,500-second function limit is about $0.5511 at that ceiling before setup/startup/storage, an estimate not a bill. Dual-architecture CUDA rebuild has a 1,200-second subprocess limit; include its actual cost. Queue wait is recorded separately from billed work. No full run is approved.

## Pilot-007 infrastructure interruption; pilot-008 reservation

Pilot-007 waited for evalnoise to stop, then image build ended after an external app shutdown with no stopping actor. No GPU request or benchmark generations. Retain its $2.50 hold and tagged cost. Reserve another $2.50 for pilot-008, aggregate holds $10.00 under the unchanged $12 cap. Use the existing audited image and CPU object files, one SM86-native rebuild (documented compatible with both approved GPUs), detached app lifecycle, and a cloud-side deadline/interlock supervisor. Supervisor cap: 0.25 cores and 1 GiB, ceiling $0.019825/hour at saved rates. Its CPU time while monitoring the queue is billed separately from unbilled GPU queueing; allow $0.023 (rounded upward) for the 4,000-second supervisor timeout, within the $2.50 reservation. A 30-minute queue timeout remains; no full run approved.

## Completed pilot-008 and current forecast

All 300 attempts completed on one NVIDIA A10 with ok status; both arms and all precisions stayed on that worker. GPU worker body 44.850405 seconds; pooled inference batches 37.814643 seconds. Saved rates and timers imply $0.00004631 inference-only per generation, or $0.00005582 for GPU/preparation/supervisor bodies (estimates excluding platform overhead).

Tagged billing at 2026-10-27T17:11:06.202272+00:00: successful retry **$0.07961645**, **$0.00026539/generation** reported to date. Whole project including earlier failures/preparation **$0.34335856**. These are gross reported amounts, not settled invoices; storage completeness is unknown. All apps stopped and no containers running.

After completed/stopped sessions and tagged review, retain $0.50 per batch for all eight attempts ($4.00 total) as conservative settling/storage allowances. Original $2.50 reservations/history remain in the ledger; this releases held funds, not alleged charges. No extra batch is launched.

Planning scenario: **$4.74–$8.14 total**, including reported spend and a $1 further setup/storage allowance. Assumptions: Llama 1B/3B per-call costs 2×/6× Qwen; four-arm pooled cost 1–2× the measured two-arm pool; A10 throughout. Stress case 3×/10× and 2× arms reaches **$11.91**. No factor is a measured Llama result or a guaranteed bound. Planning fits $12, but refine from early approved run units before committing all cells. If it will exceed October headroom, propose complete model/seed units in October and remaining units from November 1. Keep all five runs/arms/cases/models. Full run and November remain unapproved.

## Full run approved 2026-10-28

User authorized the unchanged 24,000-attempt matrix on A10 only, with a 30-minute availability cutoff, model-by-model spend/projection gates, $12 total project hard cap and completion before October 31. No fallback GPU or November execution. Runtime is the exact pilot image im-bn1uCAy12LO075Ds0NhzwA plus frozen first-party worker code; no compile/new dependency install. Each model session is separately tagged and bounded below $5 projected/reserved. Before each model, use monthly tagged spending plus an independent timer/resource upper estimate, $0.75 settling/storage buffer and the next-model projection. Refuse if the next model would cross $12. Actual execution timers enforce a model GPU envelope; the cloud supervisor stops the model/app if it reaches its envelope. Preserve incomplete cells if a cap/queue/date/operational stop occurs.

## Restarted full collection and retained interruption

Full-001 stopped after 2,936 cloud-checkpointed Qwen responses. The first shutdown reason was overwritten during cleanup, so its original trigger is unconfirmed. The reported app cost is $0.15594981, retained alongside every raw response. No Llama session started in that attempt. The total reported before full-002 was $0.49930837. Full-002 repeats the complete Qwen model matrix and will check cost before each subsequent model. The interrupted responses are excluded from the registered comparison matrix, independently of scores. The $0.50 settling hold for full-001 is an allowance, not a measured charge.

The full-002 Qwen next-model projection is $0.76599159 including its stated margin and overhead assumption. Its active GPU deadline is 12,520 seconds at the A10 worker resource ceiling, with separate setup/settling reserves. This is a stop bound, not expected runtime. Later model gates use measured completed-model throughput and reported spend.

## Qwen recovered; Llama setup interruptions

The full-002 Qwen durable checkpoint contains all 8,000 generations and the GPU completion event, despite truncation of the local result stream at 7,763. No Qwen inference was repeated. Reported app cost is $0.39501664 and timed GPU/preparation/supervisor-body estimate is $0.38869970. Gross project reporting reached $0.89432501.

The initial Llama-1B setup had a laptop connection failure before preparation, with zero generations. A subsequent attempt prepared and hashed both artifacts, but evalnoise restarted before benchmark collection. Its zero-generation app reported $0.00855848. Project total reported then was $0.90288349. Each stopped setup retains a $0.50 settling hold rather than the entire former $4.90 active-run envelope; this hold is not a measured cost. The revised next-model forecast remains about $1.33 and is checked again before launch. No other project's app is stopped.


Historical pilot holds were reviewed against fresh tagged metering and saved shutdown evidence. Retain at least $0.30 per pilot or its reported app cost plus $0.20, totaling $2.45376264. These remain allowances, not charges; absent billing rows remain unknown. The first 800-attempt Llama collection is retained as aborted for duplicate native BOS, before task scoring, with a $0.50 settling hold. Its reported app cost was $0.06342332. Known lazy-trigger replay errors in subsequent correct-transport collections count as failed observations and are never retried or excluded.

<!-- generated-full-result -->

## Completed full study

Reported gross project cost: $2.610969; cap $12.00; pilot planning range $4.74–$8.14. This snapshot is not a settled invoice. Full per-model forecasts, timings, attribution and denominators are in results/full/full-002/costs.json. Earlier failed attempts remain charged to the project.

| Batch | Recorded forecast USD | Retained hold USD | Reported USD | State |
| --- | ---: | ---: | ---: | --- |
| pilot-001 | not recorded | 0.3000 | unknown / no row | setup_rejected_before_worker |
| pilot-002 | not recorded | 0.3000 | 0.086150 | source_snapshot_rejected_before_worker |
| pilot-003 | not recorded | 0.3000 | 0.000012 | function_definition_rejected_before_worker |
| pilot-004 | not recorded | 0.3000 | 0.002404 | cpu_preparation_failed_before_generation |
| pilot-005 | not recorded | 0.3000 | 0.000029 | cancelled_during_initialization |
| pilot-006 | not recorded | 0.3000 | 0.021385 | cpu_prepared_gpu_queue_stopped_without_generation |
| pilot-007 | not recorded | 0.3538 | 0.153763 | external_app_shutdown_during_image_build |
| pilot-008 | not recorded | 0.3000 | 0.079616 | completed_300_generations_single_A10 |
| full-001-1 | 0.7660 | 0.3559 | 0.155950 | interrupted_model_restarted_whole |
| full-002-1 | 0.7660 | 0.6387 | 0.395017 | complete_cloud_checkpoint_recovered |
| full-002-2 | 1.3329 | 0.3000 | unknown / no row | setup_connection_failure_stopped |
| full-002-2-retry1 | 1.3329 | 0.3000 | 0.016424 | interlock_abort_zero_generations |
| full-002-2-retry2 | 1.3329 | 0.3000 | 0.069636 | aborted_duplicate_bos_before_scoring |
| full-002-2-native1 | 1.3329 | 0.4481 | 0.248108 | aborted_client_generator_cancellation |
| detach-probe-001 | not recorded | 0.0500 | 0.000296 | completed_after_launcher_exit |
| full-002-2-spawn1 | 1.3329 | 0.3615 | 0.161514 | interlock_abort_partial_collection |
| full-002-2-concurrent1 | 1.3329 | 0.6499 | 0.406742 | complete |
| full-002-3-concurrent1 | 3.5986 | 1.0591 | 0.813923 | complete |

Holds are allowances, not measured charges. Missing metering rows remain unknown. Project-level storage and other unattributed rows are included in the project total without being invented as per-batch charges.

<!-- /generated-full-result -->

## Approved Pythonic contract sensitivity

Additional hard cap $3, within the unchanged $12 project cap; A10 only, queue at most30 minutes, finish before October31. Two model envelopes of $1.45 plus $0.10 for settling/storage. The bounded per-model resource calculation is $1.30903 at saved rates, not measured spend. The separately frozen design has4,800 observations; all failed outcomes remain visible. Current active evalnoise follow-up must finish before the interlock permits launch. See results/ops/pythonic-001_plan.json and results/sensitivity/pythonic-001/state.json for actual execution.

<!-- generated-pythonic-cost -->

## Completed Pythonic format follow-up

Additional app metering reported to date: 0.7346155099999999 USD, including the zero-generation setup failure. Latest project reported total: 3.3455842600000008 USD; caps $3 additional/$12 project. This is not a settled invoice.

| Batch | Reported USD |
| --- | ---: |
| pythonic-001-1 | 7.732e-05 |
| pythonic-002-1 | 0.37100732 |
| pythonic-002-2 | 0.26695346 |
| pythonic-002-3 | 0.09657741 |

<!-- /generated-pythonic-cost -->
