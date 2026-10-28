"""Recover a completed cloud model checkpoint without repeating inference."""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from qunti.common import ROOT, now, read_jsonl, write_json


def validate(path, batch_id):
    events = read_jsonl(path)
    rows = [e for e in events if e['kind'] == 'generation']
    if not rows:raise RuntimeError('Cloud checkpoint contains no benchmark generations')
    protocol = json.loads((ROOT / 'configs/protocol.json').read_text())
    spec = next(s for s in json.loads((ROOT / 'configs/full_models.json').read_text()) if rows and s['model'] == rows[0]['model'])
    ids = {r['id'] for r in json.loads((ROOT / 'data/full_requests' / (spec['slug'] + '.json')).read_text())}
    expected = {(q, a, s, i) for q in protocol['precisions'] for a in protocol['arms'] for s in protocol['run_seeds'] for i in ids}
    if len(expected) != 8000:
        raise RuntimeError('Recovery requires the unchanged registered model matrix')
    keys = [(e['quant'], e['condition'], e['seed'], e['id']) for e in rows]
    done = [e for e in events if e['kind'] == 'session_finished']
    if set(keys) != expected or len(keys) != len(expected) or len(done) != 1 or sum(e['kind'] == 'session_started' for e in events) != 1:
        raise RuntimeError('Cloud checkpoint is not one complete, unique model matrix')
    if any(e['batch_id'] != batch_id or e['gpu_type'] != 'A10' or e['model_revision'] != spec['revision'] for e in rows):
        raise RuntimeError('Recovered checkpoint provenance mismatch')
    return events


def adopt(batch_id, candidate):
    events = validate(candidate, batch_id)
    folder = ROOT / 'results/full' / batch_id
    target = folder / 'events.jsonl'
    if candidate.resolve() == target.resolve():
        raise RuntimeError('Keep the cloud checkpoint separate from the original client stream')
    old = folder / 'local_stream_before_recovery.jsonl'
    if not old.exists() and target.exists(): shutil.copy2(target, old)
    shutil.copy2(candidate, target)
    prepared=next((e for e in events if e['kind']=='model_prepared'),None)
    if prepared:
        write_json(ROOT/f'results/ops/{batch_id}_model_artifacts.json',prepared['metadata'])
    write_json(folder / 'recovery.json', {'date': now(), 'source': str(candidate.relative_to(ROOT)),
               'source_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(), 'verified_generations': 8000,
               'method': 'Complete cloud matrix and GPU completion event verified; original truncated client stream retained. No inference repeated.'})
    return events


def wait_for_cloud_stop(app_id, maximum_seconds):
    deadline=datetime.now(timezone.utc)+timedelta(seconds=maximum_seconds)
    idle_since=None
    while datetime.now(timezone.utc)<deadline:
        try:
            result=subprocess.run([str(ROOT/'.venv/bin/modal'),'app','list','--json','--limit','0'],
                                  capture_output=True,text=True,check=True,timeout=45)
            app=next((a for a in json.loads(result.stdout) if a['app_id']==app_id),None)
            if app and app['state']=='stopped':return
            if app and app['tasks']=='0':
                if idle_since is None:idle_since=time.monotonic()
                if time.monotonic()-idle_since>=240:return
            else:idle_since=None
        except (subprocess.SubprocessError,ValueError):
            pass
        time.sleep(15)
    raise RuntimeError('Cloud stop wait exceeded the bounded session window; inspect app before further work')


def download_and_adopt(batch_id):
    folder = ROOT / 'results/full' / batch_id
    candidate = folder / 'cloud_events.jsonl'
    for attempt in range(3):
        temporary = folder / f'cloud_events_download_{attempt}.jsonl'
        try:
            subprocess.run([str(ROOT / '.venv/bin/modal'), 'volume', 'get', 'qunti-check-artifacts',
                            f'/full/{batch_id}/events.jsonl', str(temporary)], check=True, capture_output=True, text=True, timeout=600)
            validate(temporary, batch_id)
            temporary.replace(candidate)
            return adopt(batch_id, candidate)
        except (subprocess.SubprocessError, ValueError):
            if attempt == 2: raise
    raise RuntimeError('Unreachable recovery state')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    p.add_argument('--model-index', required=True, type=int)
    p.add_argument('--checkpoint', required=True, type=Path)
    args = p.parse_args()
    batch = f'{args.run_id}-{args.model_index}'
    events = adopt(batch, args.checkpoint.resolve())
    from scripts.full_run import RATE, CPU_RATE, SUPERVISOR_RATE, billing
    state_path = ROOT / 'results/full' / args.run_id / 'state.json'
    state = json.loads(state_path.read_text())
    row = next(r for r in state['model_sessions'] if r['batch_id'] == batch)
    done = next(e for e in events if e['kind'] == 'session_finished')
    supervisor = next(e for e in events if e['kind'] == 'supervisor_finished')
    prep = json.loads((ROOT / f'results/ops/{batch}_model_artifacts.json').read_text())
    timed = done['active_function_seconds'] * RATE / 3600 + prep.get('active_function_seconds', 0) * CPU_RATE / 3600 + (supervisor['active_function_seconds']+prep.get('preparation_supervisor_seconds',0)) * SUPERVISOR_RATE / 3600
    total, app_costs = billing(batch + '_recovered')
    actual = app_costs.get(row['app_id'])
    conservative = max(actual or 0, timed + .15)
    row.update(complete=True, attempted=8000, transport_recovered=True, reported_model_cost_usd=actual,
               timed_body_resource_cost_usd=timed, conservative_model_cost_usd=conservative, reported_project_cost_usd=total)
    state['last_reported_project_cost_usd'] = total
    write_json(state_path, state)
    ledger_path = ROOT / 'results/budget_ledger.json'
    ledger = json.loads(ledger_path.read_text())
    entry = next(r for r in ledger['batches'] if r['id'] == batch)
    entry.update(status='complete_cloud_checkpoint_recovered', metered_to_date_usd=actual,
                 timed_resource_cost_usd=timed, reservation_usd=conservative + .10)
    write_json(ledger_path, ledger)
    print(json.dumps(row, indent=2))


if __name__ == '__main__':
    main()
