"""Score the separate call-format sensitivity from durable saved outputs only."""
import argparse,json
from collections import Counter
import numpy as np
from qunti.common import ROOT,now,read_jsonl,write_json,digest
from qunti.pythonic import score_pythonic
from scripts.report_full import interval
from scripts.presentation import recovery_statement


def pct(value,bounds):return f'{100*value:.1f} [{100*bounds[0]:.1f}, {100*bounds[1]:.1f}]'

def paper_text(summary):
    if not summary['complete']:
        return 'The optional Pythonic sensitivity is incomplete; no full-design effect is estimated.'
    parts=[]
    for model in summary['models']:
        label=model.split('/')[-1].replace('-Instruct','')
        q=next(r for r in summary['scores'] if (r['model'],r['precision'],r['decoder'],r['subset'])==(model,'Q4_K_M','whole_strict','parallel'))
        old=q['primary_json_accuracy']
        recovery=next(r for r in summary['recovery_effects'] if (r['model'],r['subset'])==(model,'parallel'))
        parts.append(label+' Q4 whole-strict parallel accuracy is '+pct(q['accuracy'],q['ci95'])+r'\%, versus '+f'{100*old:.1f}'+r'\% under the original JSON contract. Its Pythonic parallel incremental recovery is '
                     +pct(recovery['net_recovery'],recovery['ci95'])+' points; the paired change in recovery versus JSON is '
                     +pct(recovery['protocol_recovery_difference'],recovery['protocol_recovery_difference_ci95'])+' points')
    gains=[r for r in summary['protocol_contrasts'] if r['precision']=='Q4_K_M' and r['decoder']=='whole_strict']
    changed=all(r['ci95'][0]>0 for r in gains)
    interpretation=('The paired Q4 contract gains are positive. ' if changed else 'The contract gains are not resolved from zero. ')
    interpretation+=recovery_statement(summary)
    interruption=summary.get('interruption_counts')
    restart=(f"Llama-3B was interrupted by the platform after {interruption['preserved']:,} durable outputs; only the missing {interruption['continued']:,} cells continued on another A10, with saved failures retained. " if interruption else '')
    return (r'\paragraph{Separate Pythonic-format sensitivity.} '
            +f"We collected {summary['observations']:,} responses on {summary['items']} cases: the original parallel subset and a separately sampled parallel-multiple subset, both Llama models, both precisions, free/whole strict and the same operational labels. "
            +'The prompt uses Meta call-list syntax without the HF tools injection, with [] for abstention. '+'; '.join(parts)+'. '
            +interpretation+' This joint prompt/parser/grammar comparison is matched only on the original parallel items. '
            +'Parallel-multiple scores are separate. Sessions differ in time and host; this is not a randomized crossover. '
            +restart+'The primary matrix is unchanged.')



def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='pythonic-002');p.add_argument('--refresh-billing',action='store_true');args=p.parse_args()
    folder=ROOT/'results/sensitivity'/args.run_id
    state=json.loads((folder/'state.json').read_text())
    if not state['complete']:raise RuntimeError('Do not report an incomplete optional design as complete')
    items=read_jsonl(ROOT/'data/pythonic/frozen.jsonl');ids=[r['id'] for r in items];byid={r['id']:r for r in items}
    protocol=json.loads((ROOT/'configs/pythonic_protocol.json').read_text());seeds=protocol['run_seeds']
    models=[r['model'] for r in state['sessions']];raw=[];scored=[];provenance=[]
    primary_state=json.loads((ROOT/'results/full/full-002/state.json').read_text())
    for session in state['sessions']:
        for source in [session['source'],*session.get('continuation_sources',[])]:
            events=read_jsonl(ROOT/source)
            prepared=next(e['metadata'] for e in events if e['kind']=='model_prepared')
            started=next(e['metadata'] for e in events if e['kind']=='session_started')
            if started['protocol_sha256']!=digest(protocol):raise RuntimeError('Recorded optional protocol hash mismatch')
            primary_session=next(r for r in primary_state['model_sessions'] if r['model']==session['model'])
            primary_events=read_jsonl(ROOT/'results/full'/primary_session['batch_id']/'events.jsonl')
            primary_prepared=next(e['metadata'] for e in primary_events if e['kind']=='model_prepared')
            same_weights=prepared['artifacts']==primary_prepared['artifacts']
            if not same_weights:raise RuntimeError('Format comparison changed the prepared weight artifacts')
            requests={r['id']:r for r in json.loads((ROOT/'data/pythonic'/(prepared['slug']+'.json')).read_text())}
            provenance.append({'model':session['model'],'same_weight_artifacts_as_primary':same_weights,'artifacts':prepared['artifacts'],
                               'source':source,'source_sha256':digest((ROOT/source).read_bytes()),'runtime':started,'resume_provenance':prepared.get('resume_provenance')})
            for e in events:
                if e['kind']!='generation':continue
                request=requests[e['id']]
                if any(e[k]!=request[k] for k in ('input_sha256','schema_sha256')) or e['prompt_sha256']!=digest(request['prompt'].encode()):
                    raise RuntimeError('Frozen optional input/prompt mismatch')
                expected_grammar=None if e['condition']=='free' else digest(request['grammars'][e['condition']].encode())
                if e['grammar_sha256']!=expected_grammar or e['gpu_type']!='A10' or e['output_contract']!='pythonic_list':
                    raise RuntimeError('Optional runtime/grammar contract mismatch')
                if e['model_revision']!=prepared['revision'] or e['llama_cpp_commit']!=started['llama_cpp_commit']:
                    raise RuntimeError('Optional source revision mismatch')
                settings=e.get('response',{}).get('generation_settings',{})
                if settings and (settings.get('temperature')!=protocol['temperature'] or settings.get('seed')!=e['seed'] or settings.get('n_predict')!=protocol['max_output_tokens']):
                    raise RuntimeError('Optional sampling settings mismatch')
                score=score_pythonic(byid[e['id']],e['text'],e['completed'])
                scored.append({**{k:e[k] for k in ('model','quant','condition','id','seed','status','completed')},'score':score})
                raw.append(e)
    lookup={(r['model'],r['quant'],r['condition'],r['id'],r['seed']):r for r in scored}
    expected={(m,q,a,i,z) for m in models for q in protocol['precisions'] for a in protocol['arms'] for i in ids for z in seeds}
    if len(raw)!=4800 or len(lookup)!=4800 or set(lookup)!=expected:raise RuntimeError('Optional matrix coverage mismatch')
    (folder/'scored.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in scored))
    primary=read_jsonl(ROOT/'results/full/full-002/scored.jsonl')
    old={(r['model'],r['quant'],r['condition'],r['id'],r['seed']):r for r in primary}
    rng=np.random.default_rng(20261028);B=10000
    subsets={'all':ids,'parallel':[r['id'] for r in items if r['category']=='parallel'],'parallel_multiple':[r['id'] for r in items if r['category']=='parallel_multiple']}
    draws={k:rng.integers(0,len(v),(B,len(v))) for k,v in subsets.items()};runs=rng.integers(0,5,(B,5))
    cells=[];effects=[];contrasts=[]
    for model in models:
        arrays={(q,a):np.array([[lookup[model,q,a,i,z]['score']['correct'] for z in seeds] for i in ids],float) for q in protocol['precisions'] for a in protocol['arms']}
        for subset,group in subsets.items():
            positions=[ids.index(i) for i in group]
            for (q,a),v in arrays.items():
                point,bounds,unused=interval(v[positions],draws[subset],runs)
                row={'model':model,'precision':q,'decoder':a,'subset':subset,'items':len(group),'observations':len(group)*5,'accuracy':point,'ci95':bounds}
                if subset=='parallel':
                    baseline=np.array([[old[model,q,a,i,z]['score']['correct'] for z in seeds] for i in group],float)
                    gain,gci,unused=interval(v[positions]-baseline,draws[subset],runs)
                    row['primary_json_accuracy']=float(baseline.mean())
                    contrasts.append({'model':model,'precision':q,'decoder':a,'subset':subset,'gain_pythonic_minus_json':gain,'ci95':gci})
                cells.append(row)
            free=arrays['F16','free']-arrays['Q4_K_M','free'];strict=arrays['F16','whole_strict']-arrays['Q4_K_M','whole_strict']
            point,bounds,unused=interval((free-strict)[positions],draws[subset],runs)
            effect={'model':model,'subset':subset,'net_recovery':point,'ci95':bounds}
            if subset=='parallel':
                baseline={k:np.array([[old[model,*k,i,z]['score']['correct'] for z in seeds] for i in group],float) for k in arrays}
                net=baseline['F16','free']-baseline['Q4_K_M','free']-baseline['F16','whole_strict']+baseline['Q4_K_M','whole_strict']
                effect['json_net_recovery']=float(net.mean())
                delta,dci,unused=interval((free-strict)[positions]-net,draws[subset],runs)
                effect['protocol_recovery_difference']=delta;effect['protocol_recovery_difference_ci95']=dci
            effects.append(effect)
    if args.refresh_billing:
        from scripts.full_run import billing
        project_cost,by_app=billing(args.run_id+'_final_sensitivity')
    else:
        snapshot=ROOT/'results/ops'/(args.run_id+'_final_sensitivity_billing.json')
        if not snapshot.exists():raise RuntimeError('Need saved billing snapshot; use --refresh-billing only for an authorized live refresh')
        project_cost=0.;by_app={}
        for row in json.loads(snapshot.read_text()):
            tags=row.get('tags') or {};tags=json.loads(tags) if isinstance(tags,str) else tags
            if tags.get('project') in ('grammar-vs-bits','qunti-check') or row.get('description') in ('grammar-vs-bits-pilot','grammar-vs-bits-full','grammar-vs-bits-artifacts','qunti-check-pilot','qunti-check-full','qunti-check-artifacts'):
                value=float(row['cost']);project_cost+=value
                by_app[row['object_id']]=by_app.get(row['object_id'],0)+value
    optional_batches=[r for r in json.loads((ROOT/'results/budget_ledger.json').read_text())['batches'] if r.get('stage')=='pythonic']
    values=[by_app.get(r.get('app_id')) for r in optional_batches]
    optional_cost=sum(values) if all(v is not None for v in values) else None
    breakdown=[{'model':m,'precision':q,'decoder':a,'observations':sum(r['model']==m and r['quant']==q and r['condition']==a for r in raw),
                'statuses':dict(Counter(r['status'] for r in raw if r['model']==m and r['quant']==q and r['condition']==a))}
               for m in models for q in protocol['precisions'] for a in protocol['arms']]
    interrupted=next((s for s in state['sessions'] if s.get('platform_interruption_retained')),None)
    result={'created_at':now(),'run_id':args.run_id,'complete':True,'separate_from_primary':True,'observations':len(raw),'items':len(ids),'models':models,
            'interruption_counts':{'preserved':interrupted['initial_attempt_observations'],'continued':interrupted['observations']-interrupted['initial_attempt_observations']} if interrupted else None,
            'status_counts':dict(Counter(r['status'] for r in raw)),'scores':cells,'recovery_effects':effects,'protocol_contrasts':contrasts,
            'status_breakdown':breakdown,'platform_interruption':state.get('continuation_note'),'failures_count_as_incorrect':True,'provenance_checks':provenance,
            'bootstrap':{'replicates':B,'seed':20261028,'unit':'Crossed original items and operational run labels; paired shared draws; pointwise unadjusted intervals'},
            'interpretation':'Joint prompt/parser/grammar contract sensitivity. Primary comparisons are limited to the identical 60 parallel items. No pooling into the primary 200; no causal attribution to syntax alone.',
            'costs':{'optional_reported_usd':optional_cost,'project_reported_usd':project_cost,'optional_cap_usd':3,'project_cap_usd':12,'settled':False,
                     'includes_failed_attempts':True,'batches':[{'batch_id':r['id'],'app_id':r.get('app_id'),'reported_usd':by_app.get(r.get('app_id'))} for r in optional_batches]}}
    write_json(folder/'summary.json',result)
    lines=['# Separate Pythonic call-format sensitivity','',result['interpretation'],'',f"{len(raw)} observations; failures retained. Status counts: {result['status_counts']}.",'',
           '| Model | Precision | Decoder | Subset | Accuracy [95% CI] |','| --- | --- | --- | --- | --- |']
    for r in cells:lines.append(f"| {r['model']} | {r['precision']} | {r['decoder']} | {r['subset']} | {pct(r['accuracy'],r['ci95'])}% |")
    lines+=['','## Matched Pythonic-minus-JSON protocol contrasts','', '| Model | Precision | Decoder | Difference [95% CI], pp |','| --- | --- | --- | --- |']
    for r in contrasts:lines.append(f"| {r['model']} | {r['precision']} | {r['decoder']} | {pct(r['gain_pythonic_minus_json'],r['ci95'])} |")
    lines+=['','## Precision interaction','', '| Model | Subset | Pythonic incremental recovery [95% CI], pp | Change versus JSON [95% CI], pp |','| --- | --- | --- | --- |']
    for r in effects:
        contrast=pct(r['protocol_recovery_difference'],r['protocol_recovery_difference_ci95']) if r['subset']=='parallel' else 'No matched JSON cohort'
        lines.append(f"| {r['model']} | {r['subset']} | {pct(r['net_recovery'],r['ci95'])} | {contrast} |")
    lines+=['','## Operational outcomes','', '| Model | Precision | Decoder | Status counts |','| --- | --- | --- | --- |']
    for r in breakdown:lines.append(f"| {r['model']} | {r['precision']} | {r['decoder']} | {r['statuses']} |")
    explanation=paper_text(result).replace(r'\paragraph{Separate Pythonic-format sensitivity.} ','').replace(r'\%','%').replace(r'\_','_')
    costs=result['costs'];lines+=['',f"Additional reported app costs: {costs['optional_reported_usd']} USD; project reported total: {costs['project_reported_usd']} USD. Caps: $3 additional/$12 project. Metering may lag.",'',explanation,'',
              'Reproduce offline: `.venv/bin/python -m scripts.report_pythonic --run-id pythonic-002`. No generated call is executed. The source JSON primary results are unchanged.','']
    (folder/'REPORT.md').write_text('\n'.join(lines))
    print('Scored the complete separate Pythonic sensitivity.')

if __name__=='__main__':main()
