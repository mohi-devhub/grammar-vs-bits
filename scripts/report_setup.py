"""Write the incomplete pilot status only from saved setup/queue/billing evidence."""
import json
from pathlib import Path
from decimal import Decimal
from qunti.common import ROOT


def main():
    summary = json.loads((ROOT / 'results/pilot/pilot-006/summary.json').read_text())
    prep = json.loads((ROOT / 'results/ops/pilot-006_model_artifacts.json').read_text())
    grammar = json.loads((ROOT / 'results/offline/grammar_validation.json').read_text())
    queue = json.loads((ROOT / 'results/ops/pilot-006_queue_final_check.json').read_text())
    billing = json.loads((ROOT / 'results/ops/project_billing.json').read_text())
    apps = json.loads((ROOT / 'results/ops/session_final_apps.json').read_text())
    containers = json.loads((ROOT / 'results/ops/session_final_containers.json').read_text())
    if summary['complete'] or summary['attempted_generations']:
        raise RuntimeError('This setup-only report must not overwrite a pilot with executed generations')
    assert all(a['state'] == 'stopped' and int(a['tasks']) == 0 for a in apps)
    assert not containers
    cost = Decimal(billing['observed_project_cost_usd'])
    text = f'''# Pilot status — incomplete; no generation results

Direction 1 is selected and unchanged. **Llama access is verified, offline validation and Qwen model preparation succeeded, but the L4 pilot did not start.** No full run has been approved or launched. Direction 2 remains the planned follow-up.

## Observed status

| Check | Saved observation |
| --- | --- |
| Selected Llama Instruct access | Both 1B and 3B: config and actual weight-file HEAD HTTP 200; LICENSE.txt retrieved and hashed |
| Offline grammar membership | {grammar['passed']:,}/{grammar['cases']:,} passed; {grammar['failed']} failed |
| Local scoring integration | Six tests passed; local and Linux dependency audits reported no known vulnerabilities |
| Qwen artifact preparation | F16, Q8_0, Q4_K_M saved with source/output hashes and commands |
| Preparation timer | {prep['active_function_seconds']:.6f} seconds, before cleanup/final volume commit |
| Executed pilot generations | {summary['attempted_generations']} of {summary['planned_generations']} planned |
| Final L4 function check | {queue['backlog']} queued input; {queue['num_total_runners']} runners; {queue['num_running_inputs']} running inputs, at {queue['captured_at']} |
| Gross project cost reported to date | ${cost:.8f}, from tagged billing captured {billing['captured_at']} |
| Shutdown | All listed apps stopped; no running containers; the only listed environment is main |

The L4 request remained queued for approximately fifteen minutes after preparation. We stopped the app at the bounded session cutoff. **The cause of the queue was not established.** A queued input here represents the entire pilot worker call, not one generated answer. Earlier setup failures and their costs are retained in the decision log, ledger and setup logs.

**Cost per generation, accuracy, recovery, confidence intervals, and the full-run cost projection are unavailable.** There are no generated responses from which to estimate them. Do not substitute zero or borrow throughput from a different GPU/model. The reported billing amount is not a settled invoice: it may lag, storage completeness is not established, and missing rows are not evidence of zero cost. ${billing['reservations_retained_usd']:.2f} remains reserved conservatively under the unchanged $12 October cap; reservations are not spending.

## What is ready and what remains

The frozen 200-case set, fixed 50-case pilot subset, schema grammars for both model families, pinned runtime/dependency locks, official AST scoring adapter and raw-event capture are implemented. Successful model preparation is recorded in [the artifact manifest](../results/ops/pilot-006_model_artifacts.json). The exact pilot runtime is recorded in [runtime metadata](../results/ops/pilot-006_runtime.json); its Python patch version differs from local orchestration and is reported explicitly.

Resume the same 300-attempt Qwen pilot when an L4 worker can start. The launcher now supports reusing the existing artifact manifest/volume, an automatic bounded queue wait, a disk-space preflight, batch-specific source snapshots, and noninteractive explicit app shutdown. Those post-session launcher safeguards have been checked locally but not demonstrated by a new paid launch. Do not reduce cases, precisions or decoder arms to force completion. Lazy-trigger serving and Llama throughput remain unmeasured.

After a completed pilot, report measured cost per generation and a forecast with explicit model/arm assumptions. If the unchanged full matrix cannot fit the remaining October project/shared budget, propose complete cells for October and the rest from November 1. Neither part is approved now. Do not ask for full-run approval on the strength of this incomplete pilot.

## Reproduce the status document

```sh
.venv/bin/python -m scripts.report_pilot --batch-id pilot-006
.venv/bin/python -m scripts.report_setup
```

Evidence: [offline checks](../results/offline/grammar_validation.json), [access/license checks](MODEL_ACCESS.json), [queue snapshot](../results/ops/pilot-006_queue_final_check.json), [tagged billing](../results/ops/project_billing.json), [app shutdown](../results/ops/session_final_apps.json), [container shutdown](../results/ops/session_final_containers.json), [setup logs](../results/ops/setup_logs), [decisions](../DECISIONS.md), [budget](../BUDGET.md).
'''
    (ROOT / 'docs/PILOT_REPORT.md').write_text(text)
    print('Wrote docs/PILOT_REPORT.md from saved evidence; no pilot metrics invented.')


if __name__ == '__main__':
    main()
