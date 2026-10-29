"""Sequential approved full study. Refuse next-model projection above the project cap."""
import argparse
import fcntl
import json
import subprocess
import time
from datetime import datetime,timezone
from pathlib import Path
from qunti.common import ROOT,now,write_json,read_jsonl
from scripts.pilot import app_snapshot,active_evalnoise

RATES=json.loads((ROOT/'results/ops/full_rates.json').read_text())
RATE=float(RATES['gpu_hour_cost_a10g'])+2*float(RATES['cpu_hour_cost'])+16*float(RATES['mem_gib_hour_cost'])
CPU_RATE=2*float(RATES['cpu_hour_cost'])+16*float(RATES['mem_gib_hour_cost'])
SUPERVISOR_RATE=.25*float(RATES['cpu_hour_cost'])+float(RATES['mem_gib_hour_cost'])


def wait_for_quiet(run_id,finish,quiet_seconds=180,allow_concurrent_studies=False):
    clear_since=None;last_busy=None
    while datetime.now(timezone.utc)<finish:
        apps=app_snapshot();busy=active_evalnoise(apps,allow_concurrent_studies)
        write_json(ROOT/f'results/ops/{run_id}_quiet_check.json',{'date':now(),'apps':apps,'required_quiet_seconds':quiet_seconds,
                   'allow_concurrent_evalnoise_studies':allow_concurrent_studies})
        if busy:
            clear_since=None;identifiers=[a['app_id'] for a in busy]
            if identifiers!=last_busy:print('Waiting for evalnoise: '+', '.join(identifiers),flush=True)
            last_busy=identifiers
        else:
            if clear_since is None:
                clear_since=time.monotonic();print('No blocking evalnoise app; checking the quiet interval before paid launch',flush=True)
            if time.monotonic()-clear_since>=quiet_seconds:return True
        time.sleep(15)
    return False

def billing(label):
    path=ROOT/f'results/ops/{label}_billing.json'
    for attempt in range(3):
        try:
            r=subprocess.run([str(ROOT/'.venv/bin/modal'),'billing','report','--for','this month','--tag-names','project,stage','--show-resources','--json'],capture_output=True,text=True,check=True,timeout=60)
            break
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
            if attempt==2:raise
            time.sleep(5)
    rows=json.loads(r.stdout);write_json(path,rows)
    total=0.0;by_app={}
    for row in rows:
        tags=row.get('tags') or {};tags=json.loads(tags) if isinstance(tags,str) else tags
        if tags.get('project') in ('grammar-vs-bits','qunti-check') or row.get('description') in ('grammar-vs-bits-pilot','grammar-vs-bits-full','grammar-vs-bits-artifacts','qunti-check-pilot','qunti-check-full','qunti-check-artifacts'):
            value=float(row['cost']);total+=value;key=row['object_id'];by_app[key]=by_app.get(key,0)+value
    return total,by_app


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='full-001')
    parser.add_argument('--resume',action='store_true',help='Continue after verified complete model checkpoints; never rerun a completed model')
    parser.add_argument('--attempt-suffix',default='',help='Unique suffix after a retained failed setup attempt')
    args=parser.parse_args()
    protocol=json.loads((ROOT/'configs/protocol.json').read_text())
    assert protocol['full_run_approved'] and protocol['execution']['gpu']=='A10'
    finish=datetime.fromisoformat(protocol['execution']['finish_by_utc'])
    pilot=json.loads((ROOT/'results/pilot/pilot-008/summary.json').read_text())
    base=pilot['projection']['qwen_main_8000_calls_resource_usd_at_observed_throughput']
    state_path=ROOT/'results/full'/args.run_id/'state.json'
    if state_path.exists() and not args.resume:
        raise RuntimeError('Run state already exists; refuse overwrite or duplicate launch')
    historical,unused=billing(args.run_id+'_initial' if not args.resume else args.run_id+'_resume')
    one_b_cost=None
    state={'run_id':args.run_id,'started_at':now(),'historical_reported_cost_usd':historical,'model_sessions':[],
           'cap_usd':12,'gpu':'A10','initial_forecast_source':'results/pilot/pilot-008/budget_forecast.json'}
    if args.resume:
        if not state_path.exists():raise RuntimeError('Cannot resume absent run state')
        state=json.loads(state_path.read_text())
        if any(not r['complete'] for r in state['model_sessions']):
            raise RuntimeError('Recover and audit the incomplete checkpoint before resuming; do not silently rerun it')
        for key in ('stop_reason','finished_at'):
            if key in state:state.setdefault('previous_stops',[]).append({key:state.pop(key)})
        state.setdefault('resumed_at',[]).append(now())
    committed_upper=max(historical,state['historical_reported_cost_usd']+sum(r['conservative_model_cost_usd'] for r in state['model_sessions']+state.get('failed_model_attempts',[])))
    if state['model_sessions']:
        events=read_jsonl(ROOT/'results/full'/state['model_sessions'][0]['batch_id']/'events.jsonl')
        base=sum(e['batch_wall_seconds'] for e in events if e['kind']=='run_finished')*RATE/3600
    if len(state['model_sessions'])>1:
        events=read_jsonl(ROOT/'results/full'/state['model_sessions'][1]['batch_id']/'events.jsonl')
        one_b_cost=sum(e['batch_wall_seconds'] for e in events if e['kind']=='run_finished')*RATE/3600
    completed_models=len(state['model_sessions'])
    write_json(state_path,state)
    for index,spec in enumerate(json.loads((ROOT/'configs/full_models.json').read_text())):
        if index<completed_models:
            if state['model_sessions'][index]['model']!=spec['model']:
                raise RuntimeError('Resume model order differs from the frozen protocol')
            continue
        if datetime.now(timezone.utc)>=finish:
            state['stop_reason']='Finish cutoff reached';break
        if not wait_for_quiet(args.run_id,finish,allow_concurrent_studies=protocol['execution'].get('allow_concurrent_evalnoise_studies',False)):
            state['stop_reason']='Finish cutoff reached while waiting for evalnoise';break
        current,by_app=billing(args.run_id+f'_before_model_{index}')
        known=max(current,committed_upper)
        # First four-arm model calibrates later-model throughput. Model factors are assumptions.
        multiplier=(1,2,6)[index]
        projected_base=base*multiplier
        if index==2 and one_b_cost is not None:projected_base=max(projected_base,one_b_cost*3)
        projected=projected_base*1.5+0.20
        gate={'model':spec['model'],'reported_project_cost_usd':current,'conservative_project_cost_usd':known,
              'next_model_projection_usd':projected,'settling_storage_buffer_usd':0.75,'date':now()}
        write_json(ROOT/f'results/ops/{args.run_id}_{spec["slug"]}_budget_gate.json',gate)
        if known+projected+0.75>12:
            state['stop_reason']='Next-model projection would cross $12 with buffer';state['refused_model']=spec['model'];break
        if projected>5:
            state['stop_reason']='Next model projected over $5 batch threshold';state['refused_model']=spec['model'];break
        envelope=min(4.75,12-known-0.75-0.20)
        if envelope<projected:
            state['stop_reason']='Insufficient bounded execution envelope for next model';break
        gpu_seconds=int((envelope-0.15)*3600/RATE)
        gpu_seconds=min(gpu_seconds,int((finish-datetime.now(timezone.utc)).total_seconds())-2100)
        if gpu_seconds<120:
            state['stop_reason']='Not enough time before finish cutoff';break
        batch=f'{args.run_id}-{index+1}'+('-'+args.attempt_suffix if args.attempt_suffix else '')
        ledger_path=ROOT/'results/budget_ledger.json'
        with (ROOT/'.cache/budget.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            ledger=json.loads(ledger_path.read_text())
            if any(x['id']==batch for x in ledger['batches']):raise RuntimeError('Duplicate model session ID; do not repeat data silently')
            reserve=envelope+0.15
            if sum(x['reservation_usd'] for x in ledger['batches'])+reserve>12:
                state['stop_reason']='Conservative reservation ledger cannot fit next model';write_json(state_path,state);return
            ledger['batches'].append({'id':batch,'model':spec['model'],'stage':'full','reserved_at':now(),'reservation_usd':reserve,
                                      'projected_cost_usd':projected,'status':'reserved','invoice_cost_usd':None,'gpu_deadline_seconds':gpu_seconds})
            write_json(ledger_path,ledger)
        log=ROOT/'.cache'/f'{batch}.log'
        with log.open('w') as out:
            proc=subprocess.run([str(ROOT/'.venv/bin/python'),'-m','scripts.full_model','--slug',spec['slug'],'--batch-id',batch,'--gpu-seconds',str(gpu_seconds)],stdout=out,stderr=subprocess.STDOUT)
        folder=ROOT/'results/full'/batch
        events=read_jsonl(folder/'events.jsonl') if (folder/'events.jsonl').exists() else []
        generations=[e for e in events if e['kind']=='generation']
        done=next((e for e in events if e['kind']=='session_finished'),None)
        prep_path=ROOT/f'results/ops/{batch}_model_artifacts.json'
        prep=json.loads(prep_path.read_text()) if prep_path.exists() else {}
        supervisor=next((e for e in events if e['kind']=='supervisor_finished'),{})
        timed=(done['active_function_seconds']*RATE/3600+
               prep.get('active_function_seconds',0)*CPU_RATE/3600+(supervisor.get('active_function_seconds',0)+prep.get('preparation_supervisor_seconds',0))*SUPERVISOR_RATE/3600) if done else None
        current,by_app=billing(batch+'_after')
        info_path=ROOT/f'results/ops/{batch}_app.json';info=json.loads(info_path.read_text()) if info_path.exists() else {}
        actual=by_app.get(info.get('app_id'))
        conservative=max(actual or 0,(timed+0.15) if timed is not None else envelope+0.15)
        committed_upper+=conservative
        session={'batch_id':batch,'model':spec['model'],'attempted':len(generations),'complete':len(generations)==8000 and done is not None,
                 'exit_code':proc.returncode,'reported_model_cost_usd':actual,'timed_body_resource_cost_usd':timed,
                 'conservative_model_cost_usd':conservative,'reported_project_cost_usd':current,'app_id':info.get('app_id')}
        state['model_sessions'].append(session);state['last_reported_project_cost_usd']=current
        ledger=json.loads(ledger_path.read_text());entry=next(b for b in ledger['batches'] if b['id']==batch)
        entry.update(app_id=info.get('app_id'),status='complete' if session['complete'] else 'incomplete',
                     metered_to_date_usd=actual,timed_resource_cost_usd=timed,original_reservation_usd=entry['reservation_usd'],
                     reservation_usd=conservative+0.10)
        write_json(ledger_path,ledger);write_json(state_path,state)
        print(json.dumps(session),flush=True)
        if not session['complete'] or proc.returncode:
            state['stop_reason']='Model session incomplete or operationally failed';break
        if index==0:
            base=sum(e['batch_wall_seconds'] for e in events if e['kind']=='run_finished')*RATE/3600
        if index==1:one_b_cost=sum(e['batch_wall_seconds'] for e in events if e['kind']=='run_finished')*RATE/3600
        if max(current,committed_upper)+0.75>=12:
            state['stop_reason']='Project spend guard reached after model';break
    state['finished_at']=now();state['complete']=len(state['model_sessions'])==3 and all(x['complete'] for x in state['model_sessions'])
    write_json(state_path,state)
    print(json.dumps(state,indent=2),flush=True)


if __name__=='__main__':main()
