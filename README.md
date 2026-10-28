# Quantization and tool-call recovery

Public repository: https://github.com/mohi-devhub/qunti-check. This is a conceptual replication. The original code is MIT licensed; see LICENSE and THIRD_PARTY_NOTICES.md for benchmark attribution.

**Completed study:** 24,000 generations in the design frozen before execution across three small models, two weight precisions, four decoder arms and five operational runs. Gross project metering reported to date is **$3.345584**, including setup failures and interrupted collections, against a **$12 cap**. Metering may lag.

[Results and interpretation](docs/FULL_REPORT.md) · [All scores and paired 95% CIs](results/full/full-002/REPORT.md) · [Cost accounting](results/full/full-002/COSTS.md) · [Paper PDF](paper/main.pdf) · [Learning notes](LEARNING.md)

The question is whether whole-response schema enforcement recovers a quantization gap that permissive or trigger-gated grammars fail to recover. This is a conceptual replication. Its estimand subtracts the effect constraints already have at F16; it does not causally divide quantization damage into syntax and meaning. Direction 2 remains the planned, unevaluated follow-up.

## Study design

The anchors are Qwen3-0.6B, Llama-3.2-1B-Instruct and Llama-3.2-3B-Instruct. Every cell uses the same 200 frozen BFCL cases, including 180 required-call cases and 20 irrelevance diagnostics. Selection never depends on baseline success.

Weights are F16 GGUF or Q4_K_M generated from the same F16 export. K/V caches stay F16. Free, loose, trigger-strict and whole-strict arms share each model's declared prompt. Temperature is zero, with four server slots, 4,096 context tokens per slot, 512 output tokens and five seed/schedule labels frozen before execution. Greedy repeats remain paired with their original items.

For Llama, the pinned HF single-object JSON template was extended with a system-level JSON-array convention for parallel calls. Its later single-object instruction conflicts with that extension. The primary findings are conditional on this declared JSON contract; Meta also documents a Pythonic call-list format. Exact templates and the separate Pythonic sensitivity are documented in the paper and data/pythonic/manifest.json.

The allocation selector stays `A10`, with no GPU fallback. Exact device names and drivers are retained per item. Each complete primary model matrix uses one worker session. Interrupted collections remain separate and are never silently pooled into it.

- [Protocol and estimands](docs/PROTOCOL_NOTES.md), [model licenses/access](docs/MODELS.md), [GPU naming](docs/GPU_NAMING.md).
- [Related work](docs/RELATED_WORK.md), [direction audit and planned follow-up](docs/DIRECTIONS.md).
- [Budget](BUDGET.md), [decisions and corrections](DECISIONS.md), [frozen data manifest](data/manifest.json).

## Rebuild the saved results without model inference

Use Python 3.12.12 and uv 0.9.7 from their official releases. The environment belongs to this repository. Python dependencies and wheels are pinned in uv.lock and the hash-bearing requirements lockfiles.

```sh
uv sync --frozen --group analysis --no-build
.venv/bin/python -m scripts.fetch_sources
.venv/bin/python -m scripts.verify_provenance
.venv/bin/python -m scripts.audit_full --run-id full-002
.venv/bin/python -m scripts.report_full --run-id full-002
.venv/bin/python -m scripts.report_transitions --run-id full-002
.venv/bin/python -m scripts.report_failure_sensitivity --run-id full-002
.venv/bin/python -m scripts.plot_full --run-id full-002
.venv/bin/python -m scripts.build_paper_data --run-id full-002
.venv/bin/python -m scripts.fetch_paper_toolchain
.venv/bin/python -m scripts.compile_paper --run-id full-002
.venv/bin/python -m pytest -q
.venv/bin/python -m pip_audit --local --format json --output results/ops/pip-audit-local-reproduction.json
```

These commands use saved raw outputs and require no model job or Modal credential. Source and TeX downloads use the recorded official URLs and SHA-256 hashes. The macOS TeX toolchain stays under .cache/paper-tex; shell escape is disabled. Keep saved costs.json and billing snapshots when rebuilding the historical paper. The separate report_full_costs command refreshes live account metering and is not part of offline reproduction.

The scorer calls the pinned official BFCL AST checker without executing generated calls. Irrelevance uses the unchanged official helper. Structural validity, official correctness, incomplete output and operational errors remain separate fields. Primary CIs use crossed paired item/run resampling; item-only intervals are included as a sensitivity check. Intervals are pointwise and unadjusted.

The [failure breakdown and exclusion sensitivity](results/full/full-002/FAILURE_SENSITIVITY.md) uses saved outputs only. It reports cell-only exclusions, matched item/run exclusions and complete-item exclusions. These are post-hoc checks that condition on completion; the failure-inclusive analysis frozen before execution remains primary.

## Rebuild the offline grammar check

The recorded gate passed 6,194 finite membership checks using the actual llama.cpp validator. This checks strings, not every token-level serving behavior.

```sh
uv sync --frozen --group analysis --group build --no-build
.venv/bin/cmake -S vendor/llama.cpp -B .cache/llama-validator-build -G Ninja -DCMAKE_MAKE_PROGRAM="$PWD/.venv/bin/ninja" -DGGML_METAL=OFF -DGGML_ACCELERATE=OFF -DGGML_BLAS=OFF -DGGML_OPENMP=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_SERVER=OFF -DLLAMA_BUILD_TOOLS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_TESTS=ON -DCMAKE_BUILD_TYPE=Release
.venv/bin/cmake --build .cache/llama-validator-build --target test-gbnf-validator --parallel 4
.venv/bin/python -m scripts.validate_grammars --validator .cache/llama-validator-build/bin/test-gbnf-validator
```

The validator can exit zero for rejection, so the harness checks its explicit membership message. Constraints use the offered schemas without consulting gold function names, values or call counts. The loose arm deliberately has an unrestricted-text escape. Whole strict has no such escape and permits an explicit NO_CALL response.

## Reproduce inference as a separately authorized campaign

The primary design was frozen before execution, without a public preregistration timestamp. Historical machine-readable field names containing "registered" are bookkeeping labels, not a public-registration claim. The original study is complete. These commands make paid calls; do not rerun a completed batch inadvertently. A new campaign needs its own authorized dates, budget and unique run ID. The original October cutoff prevents accidental later execution until those settings are deliberately updated.

Authenticate Modal and obtain access to the official publisher repositories. The Modal secret `huggingface` must contain read-only HF_TOKEN. It is injected only into model preparation; never paste or print it. Model weights and credentials are excluded from the release.

```sh
.venv/bin/python -m scripts.prepare_full
.venv/bin/python -m scripts.full_run --run-id UNIQUE_AUTHORIZED_RUN
```

The executed runtime reuses the audited image im-bn1uCAy12LO075Ds0NhzwA plus a frozen worker-source copy. Another Modal account can set `QUNTI_REBUILD_FROM_SOURCE=1` on the full_run command to use the pinned official recipe in cloud.py. Recheck that account's rates, model access, deadlines and budget before authorizing it.

The engine is official llama.cpp at 8542e94350f0ade01644db6f1d1520da3814dafd. BFCL source/data are official ShishirPatil/gorilla at 6ea57973c7a6097fd7c5915698c54c17c5b1b6c8. Model revisions, source/artifact hashes, commands and actual runtime versions are retained in results/ops. The cloud Python patch version is recorded separately from local Python.

The controller checks attributed spend and the next-model projection, reserves a bounded envelope, and refuses duplicate session IDs. Queue wait is limited to 30 minutes. It submits a spawned cloud job so collection does not depend on a live laptop stream. The cloud checkpoints every event and stops the app at completion or a guard failure. A complete checkpoint can be adopted after delivery failure; an incomplete one is not declared successful. The evalnoise scheduling rule and all later corrections are in DECISIONS.md.

Llama uses publisher token IDs to avoid adding a second BOS marker. Known lazy-trigger replay errors count as incorrect operational outcomes without retrying. Unknown request/configuration errors stop the worker. Token limits remain failed attempts. No arm, case or run is dropped to make costs or scores look better.

## Locate the release artifacts

- results/full/full-002/state.json maps models to their primary batch IDs.
- results/full/BATCH/events.jsonl contains raw per-item outputs and setup/completion metadata.
- results/full/full-002/summary.json, scored.jsonl, diagnostics.csv and transitions.json contain derived metrics.
- figures/ comes only from the saved summary; paper/generated/ comes only from saved results and costs.
- results/ops contains pinned provenance, audits, billing snapshots, interrupted-attempt inventories and shutdown evidence.

After collection, the local finalizer can build the deliverables:

```sh
.venv/bin/python -m scripts.finalize_study --run-id full-002
.venv/bin/python -m scripts.archive_cloud --run-id full-002
.venv/bin/python -m scripts.cleanup_model_cache --run-id full-002
.venv/bin/python -m scripts.package_release --run-id full-002
```

The cloud archive preserves outputs and provenance with byte counts and SHA-256 hashes; it excludes reproducible model caches and does not delete remote data. The optional cleanup command verifies every archived file before removing regenerable GGUF weights from this project's stopped volume. It retains model manifests and raw cloud outputs. The local release archive excludes weights, dependency caches and credentials. Packaging does not publish anything. Verify the resulting archive with `.venv/bin/python -m scripts.verify_release --run-id full-002`.

This is a small single-turn BFCL conceptual replication, not a complete leaderboard or a multi-turn agent execution study. Format guarantees do not guarantee the right tool or argument value. Signed effects, unstable/undefined shares, null results and negative results are retained.

## Executed code and optional format sensitivity

provenance/executed-workers/ contains exact worker snapshots and their original hashes for all primary sessions. The root qunti/ code is the maintained implementation. Historical launcher revisions were not retained; commands and runtime metadata are preserved.

The separately approved Pythonic sensitivity uses 60 original parallel cases plus 60 frozen parallel_multiple cases, both Llama models, F16/Q4_K_M, free/whole strict and all five run labels. Its $3 additional cap remains within the project $12 cap. It is never pooled into the primary matrix. [Contract and analysis details](docs/PYTHONIC_SENSITIVITY.md) distinguish the matched parallel comparison from the new parallel_multiple endpoint. Prepare and validate with `.venv/bin/python -m scripts.prepare_pythonic`; paid execution is `.venv/bin/python -m scripts.run_pythonic --run-id UNIQUE_AUTHORIZED_ID`. These commands enforce the original October cutoff. Analyze saved completed outputs with `.venv/bin/python -m scripts.report_pythonic --run-id pythonic-002`.

The raw outputs are also distributed in the repository release archive. Published releases and checksums are listed at https://github.com/mohi-devhub/qunti-check/releases. Historical audit findings and their resolution are in AUDIT.md and docs/AUDIT_RESOLUTION.md.

The additional Pythonic format sensitivity is complete and reported separately in [its report](results/sensitivity/pythonic-002/REPORT.md). It does not replace the primary matrix.
