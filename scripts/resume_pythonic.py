"""Complete only missing optional cells after a retained platform interruption."""
import argparse,json,subprocess
from datetime import datetime,timezone
from qunti.common import ROOT,now,read_jsonl,write_json
from scripts.pilot import app_snapshot,active_evalnoise,freeze_worker_source
from scripts.full_run import billing,RATE,CPU_RATE,SUPERVISOR_RATE


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='pythonic-002');args=p.parse_args()
    folder=ROOT/'results/sensitivity'/args.run_id;path=folder/'state.json';state=json.loads(path.read_text())
    if state['complete'] or len(state['sessions'])!=2 or state['sessions'][1]['complete']:raise RuntimeError('Not the retained interrupted design')
    batch=args.run_id+'-3'
    if (folder/(batch+'_app.json')).exists():raise RuntimeError('Never repeat a submitted continuation')
    apps=app_snapshot()
    if active_evalnoise(apps,True) or any(a['state']!='stopped' and a['description'].startswith('qunti-check') for a in apps):raise RuntimeError('Scheduling interlock')
    protocol=json.loads((ROOT/'configs/pythonic_protocol.json').read_text())
    cutoff=datetime.fromisoformat(protocol['execution']['finish_by_utc'])
    if (cutoff-datetime.now(timezone.utc)).total_seconds()<7500:raise RuntimeError('October cutoff')
    ledgerpath=ROOT/'results/budget_ledger.json';ledger=json.loads(ledgerpath.read_text())
    total,byapp=billing(batch+'_before')
    bounds=[]
    # Closed app lifetime bounds all GPU, preparation and supervisor resources
    # simultaneously, plus 180 seconds startup allowance. This deliberately
    # overcounts their sequential lifetimes, without treating live metering as final.
    for row in ledger['batches']:
        if row.get('stage')!='pythonic':continue
        app=next(a for a in apps if a['app_id']==row['app_id'])
        if app['state']!='stopped' or not app.get('stopped_at'):raise RuntimeError('Previous optional app not stopped')
        elapsed=(datetime.fromisoformat(app['stopped_at'])-datetime.fromisoformat(app['created_at'])).total_seconds()
        bound=max(byapp.get(row['app_id'],0),(elapsed+180)*(RATE+CPU_RATE+SUPERVISOR_RATE)/3600)
        bounds.append({'app_id':row['app_id'],'closed_app_seconds':elapsed,'conservative_usd':bound,'reported_usd':byapp.get(row['app_id'])})
    upper=1.35;prior=sum(r['conservative_usd'] for r in bounds)
    if prior+upper+.1>3 or total+upper+.75>12 or sum(r['reservation_usd'] for r in ledger['batches'])+upper>12:raise RuntimeError('Continuation does not fit the approved caps')
    interrupted=state['sessions'][1];source=ROOT/interrupted['source'];rows=[r for r in read_jsonl(source) if r['kind']=='generation']
    keys={(r['quant'],r['condition'],r['seed'],r['id']) for r in rows}
    expected={(q,a,z,r['id']) for q in protocol['precisions'] for a in protocol['arms'] for z in protocol['run_seeds'] for r in read_jsonl(ROOT/'data/pythonic/frozen.jsonl')}
    if len(keys)!=len(rows) or not keys<expected:raise RuntimeError('Invalid retained checkpoint')
    missing=len(expected-keys)
    write_json(folder/'preemption_state.json',state)
    write_json(folder/(batch+'_gate.json'),{'date':now(),'reason':'Platform internal failure/preemption; complete only cells without a durable prediction',
                'retained_observations':len(rows),'missing_observations':missing,'closed_app_bounds':bounds,'prior_optional_bound_usd':prior,
                'new_resource_envelope_usd':upper,'additional_bound_with_storage_buffer_usd':prior+upper+.1,'project_reported_usd':total,'gpu':'A10'})
    ledger['batches'].append({'id':batch,'stage':'pythonic','model':interrupted['model'],'reserved_at':now(),'reservation_usd':upper,'projected_cost_usd':None,'status':'reserved_continuation'})
    write_json(ledgerpath,ledger);freeze_worker_source(batch)
    with (ROOT/'.cache'/(batch+'.log')).open('w') as log:
        outcome=subprocess.run([str(ROOT/'.venv/bin/python'),'-m','scripts.run_pythonic_model','--batch-id',batch,'--slug','Llama-3.2-3B-Instruct','--resume-from',interrupted['source']],stdout=log,stderr=subprocess.STDOUT)
    info=json.loads((folder/(batch+'_app.json')).read_text());app_id=info['app_id']
    ledger=json.loads(ledgerpath.read_text());entry=next(r for r in ledger['batches'] if r['id']==batch);entry['app_id']=app_id
    events=read_jsonl(folder/(batch+'.jsonl')) if (folder/(batch+'.jsonl')).exists() else []
    new=[r for r in events if r['kind']=='generation'];newkeys=[(r['quant'],r['condition'],r['seed'],r['id']) for r in new]
    complete=outcome.returncode==0 and len(newkeys)==len(set(newkeys))==missing and set(newkeys)==expected-keys and any(r['kind']=='session_finished' for r in events)
    entry['status']='complete_continuation' if complete else 'incomplete_continuation';write_json(ledgerpath,ledger)
    write_json(folder/(batch+'_completion.json'),{'date':now(),'complete':complete,'observations':len(new),'expected_missing':missing,'app_id':app_id})
    if not complete:raise RuntimeError('Continuation incomplete; retain both checkpoints and stop')
    interrupted.update(initial_attempt_observations=len(rows),observations=len(rows)+len(new),complete=True,
                       continuation_sources=[str((folder/(batch+'.jsonl')).relative_to(ROOT))],continuation_app_ids=[app_id],
                       collection_sessions=2,platform_interruption_retained=True)
    state.update(complete=True,finished_at=now(),continuation_note='Llama-3B platform interruption retained. Only cells without durable outputs continued on another A10; no saved failed response was retried.')
    write_json(path,state);print('Completed missing optional cells without replacing saved outcomes.',flush=True)

if __name__=='__main__':main()
