"""Sequential detached optional sensitivity with $3 additional/$12 project guards."""
import argparse,fcntl,json,subprocess,time
from datetime import datetime,timezone
import modal
from qunti.common import ROOT,now,write_json,read_jsonl
from scripts.full_run import billing,RATE,CPU_RATE,SUPERVISOR_RATE
from scripts.pilot import app_snapshot,active_evalnoise,freeze_worker_source
from scripts.recover_full_model import wait_for_cloud_stop

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='pythonic-001');p.add_argument('--resume',action='store_true');args=p.parse_args()
    out=ROOT/'results/sensitivity'/args.run_id;out.mkdir(parents=True,exist_ok=True)
    statepath=out/'state.json'
    if statepath.exists() and not args.resume:raise RuntimeError('Refuse accidental rerun of an existing sensitivity campaign')
    gate=json.loads((ROOT/'results/offline/pythonic_validation.json').read_text())
    if gate['failed']:raise RuntimeError('Offline grammar gate failed')
    protocol=json.loads((ROOT/'configs/pythonic_protocol.json').read_text())
    specs=json.loads((ROOT/'data/pythonic/manifest.json').read_text())['models']
    state={'run_id':args.run_id,'started_at':now(),'complete':False,'optional_cap_usd':3,'project_cap_usd':12,'sessions':[]}
    if args.resume:
        state=json.loads(statepath.read_text())
        if any(not r['complete'] for r in state['sessions']):raise RuntimeError('Recover an incomplete optional session before resuming')
    write_json(statepath,state)
    deadline=datetime.fromisoformat(protocol['execution']['finish_by_utc'])
    for index,spec in enumerate(specs):
        if index<len(state['sessions']):continue
        batch=args.run_id+'-'+str(index+1)
        while active_evalnoise(app_snapshot(),True):
            if datetime.now(timezone.utc)>=deadline:raise RuntimeError('October cutoff while waiting for evalnoise')
            print('Waiting for the existing evalnoise follow-up to finish',flush=True);time.sleep(30)
        if datetime.now(timezone.utc)>=deadline:raise RuntimeError('October cutoff reached')
        total,byapp=billing(batch+'_before')
        all_batches=json.loads((ROOT/'results/budget_ledger.json').read_text())['batches']
        optional_batches=[r for r in all_batches if r.get('stage')=='pythonic']
        prior=sum(max(byapp.get(r.get('app_id'),0),r['reservation_usd']) for r in optional_batches)
        modelcost=next(r['reported_model_cost_usd'] for r in json.loads((ROOT/'results/full/full-002/costs.json').read_text())['models'] if r['model']==spec['model'])
        projection=modelcost*2400/8000*2+.2
        upper=1.35
        if prior+upper+.1>3 or total+upper+.75>12:raise RuntimeError('Optional/project cap refuses the next model')
        if (deadline-datetime.now(timezone.utc)).total_seconds()<7500:raise RuntimeError('Insufficient time before cutoff')
        # Ceiling includes two 2,500-second GPU bodies, startup allowance, bounded preparation and supervisors.
        bound=((2700+180)*RATE+1800*CPU_RATE+7200*SUPERVISOR_RATE)/3600+.1
        if bound>upper:raise RuntimeError('Resource ceiling exceeds the per-model envelope')
        write_json(out/(batch+'_gate.json'),{'date':now(),'project_reported_usd':total,'optional_prior_usd':prior,
                    'projection_usd':projection,'resource_envelope_usd':upper,'resource_ceiling_calculation_usd':bound,'gpu':'A10','queue_wait_seconds':1800})
        ledgerpath=ROOT/'results/budget_ledger.json'
        with (ROOT/'.cache/budget.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);ledger=json.loads(ledgerpath.read_text())
            if any(r['id']==batch for r in ledger['batches']):raise RuntimeError('Duplicate batch ID')
            if sum(r['reservation_usd'] for r in ledger['batches'])+upper>12:raise RuntimeError('Reservation cap exceeded')
            ledger['batches'].append({'id':batch,'stage':'pythonic','model':spec['model'],'reserved_at':now(),'reservation_usd':upper,'projected_cost_usd':projection,'status':'reserved'})
            write_json(ledgerpath,ledger)
        freeze_worker_source(batch)
        # Each CLI child gets a fresh import/image snapshot for its model.
        command=[str(ROOT/'.venv/bin/python'),'-m','scripts.run_pythonic_model','--batch-id',batch,'--slug',spec['slug']]
        with (ROOT/'.cache'/(batch+'.log')).open('w') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        appinfo=json.loads((out/(batch+'_app.json')).read_text())
        app_id=appinfo['app_id']
        ledger=json.loads(ledgerpath.read_text())
        next(r for r in ledger['batches'] if r['id']==batch)['app_id']=app_id
        write_json(ledgerpath,ledger)
        events=read_jsonl(out/(batch+'.jsonl')) if (out/(batch+'.jsonl')).exists() else []
        rows=[r for r in events if r['kind']=='generation']
        expected={(q,a,z,i['id']) for q in protocol['precisions'] for a in protocol['arms'] for z in protocol['run_seeds'] for i in read_jsonl(ROOT/'data/pythonic/frozen.jsonl')}
        actual=[(r['quant'],r['condition'],r['seed'],r['id']) for r in rows]
        finished=[r for r in events if r['kind']=='session_finished']
        complete=result.returncode==0 and len(rows)==2400 and len(set(actual))==2400 and set(actual)==expected and len(finished)==1
        if any(r['gpu_type']!='A10' or r['model_revision']!=spec['revision'] for r in rows):raise RuntimeError('Runtime pin mismatch')
        total,byapp=billing(batch+'_after');actualcost=byapp.get(app_id)
        state['sessions'].append({'batch_id':batch,'model':spec['model'],'app_id':app_id,'observations':len(rows),'complete':complete,
                                   'reported_cost_usd':actualcost,'conservative_cost_usd':upper,'source':str((out/(batch+'.jsonl')).relative_to(ROOT))})
        state['project_reported_cost_usd']=total
        reported=[byapp.get(r['app_id']) for r in state['sessions']]
        state['optional_reported_cost_usd']=sum(reported) if all(v is not None for v in reported) else None
        write_json(statepath,state)
        if total>=12 or (state['optional_reported_cost_usd'] is not None and state['optional_reported_cost_usd']>=3):raise RuntimeError('Spend ceiling reached; stop')
        if not complete:raise RuntimeError('Incomplete optional model; retain observations and stop without replacing it')
    state['complete']=True;state['finished_at']=now();write_json(statepath,state)
    print('Completed 4,800 separate Pythonic sensitivity observations.',flush=True)

if __name__=='__main__':main()
