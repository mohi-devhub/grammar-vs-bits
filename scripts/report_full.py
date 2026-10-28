"""Official scores and paired item-cluster bootstrap; no synthetic result filling."""
import argparse
import json
import csv
from collections import Counter
from pathlib import Path
import numpy as np
from qunti.common import ROOT,read_jsonl,write_json,now
from qunti.scoring import score
from qunti.diagnostics import taxonomy


def interval(values,indices,run_indices=None):
    values=np.asarray(values,dtype=float)
    if run_indices is not None and values.ndim==2:
        weights=np.zeros((len(run_indices),values.shape[1]))
        for r in range(values.shape[1]):weights[:,r]=(run_indices==r).sum(axis=1)/run_indices.shape[1]
        boot=np.einsum('bir,br->b',values[indices],weights)/indices.shape[1]
        return float(values.mean()),[float(x) for x in np.quantile(boot,[.025,.975])],boot
    means=np.asarray(values,dtype=float).mean(axis=1) if np.asarray(values).ndim==2 else np.asarray(values,dtype=float)
    boot=means[indices].mean(axis=1)
    return float(means.mean()),[float(x) for x in np.quantile(boot,[.025,.975])],boot


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='full-001');args=p.parse_args()
    protocol=json.loads((ROOT/'configs/protocol.json').read_text())
    specs=json.loads((ROOT/'configs/full_models.json').read_text())
    items=read_jsonl(ROOT/'data/frozen.jsonl');by_id={i['id']:i for i in items};ids=[i['id'] for i in items]
    seeds=protocol['run_seeds'];arms=protocol['arms'];quants=protocol['precisions']
    base=ROOT/'results/full'/args.run_id;base.mkdir(parents=True,exist_ok=True)
    state=json.loads((base/'state.json').read_text())
    batches={r['model']:r['batch_id'] for r in state['model_sessions']}
    rows=[];seen=set();metrics={};statuses={};timings=[]
    with (base/'scored.jsonl').open('w') as out:
        for model_index,spec in enumerate(specs):
            batch=batches.get(spec['model'],f'{args.run_id}-{model_index+1}')
            source=ROOT/'results/full'/batch/'events.jsonl'
            if not source.exists():continue
            for line in source.open():
                if not line.strip():continue
                event=json.loads(line)
                if event['kind'] in ('run_finished','session_finished','supervisor_finished','budget_stop'):
                    timings.append({'model':spec['model'],**event})
                if event['kind']!='generation':continue
                key=(event['model'],event['quant'],event['condition'],event['seed'],event['id'])
                if key in seen:raise RuntimeError('Duplicate full-run observation; never silently pool retries')
                seen.add(key)
                result=score(by_id[event['id']],event['text'],family=spec['family'],completed=event['completed'])
                diag=taxonomy(by_id[event['id']],event['text'],result,family=spec['family'])
                slim={k:event[k] for k in ('model','model_revision','family','quant','condition','seed','id','category','status','completed','gpu_type','gpu_name','batch_id')}
                slim.update(score=result,taxonomy=diag,raw_source=str(source.relative_to(ROOT)))
                out.write(json.dumps(slim,ensure_ascii=False)+'\n')
                metrics[key]={'correct':float(result['correct']),'invalid_json_or_format':float(result['invalid_json_or_format']),
                              'schema_valid':float(result['schema_valid']),**{f'error_{k}':float(v) for k,v in diag['flags'].items()},
                              **{'operational_'+s:float(event['status']==s) for s in ('grammar_trigger_replay_error','token_limit','request_error','context_overflow')}}
                statuses[key]=event['status'];rows.append(slim)
    rng=np.random.default_rng(protocol['execution']['bootstrap_seed'])
    reps=protocol['execution']['bootstrap_replicates']
    subsets={'all':ids,'required':[i['id'] for i in items if i['category']!='irrelevance']}
    subsets.update({cat:[i['id'] for i in items if i['category']==cat] for cat in sorted({i['category'] for i in items})})
    indices={name:rng.integers(0,len(sub),(reps,len(sub))) for name,sub in subsets.items()}
    run_indices=rng.integers(0,len(seeds),(reps,len(seeds)))
    tables=[];recoveries=[];contrasts=[]
    for spec in specs:
        arrays={}
        for quant in quants:
            for arm in arms:
                keys=[(spec['model'],quant,arm,seed,item) for item in ids for seed in seeds]
                present=[k for k in keys if k in metrics]
                row={'model':spec['model'],'precision':quant,'decoder':arm,'expected_attempts':len(keys),
                     'observed_attempts':len(present),'complete':len(present)==len(keys),
                     'status_counts':dict(Counter(statuses[k] for k in present))}
                if row['complete']:
                    values=np.array([[metrics[(spec['model'],quant,arm,seed,item)]['correct'] for seed in seeds] for item in ids])
                    arrays[quant,arm]=values
                    row['scores']={}
                    for name,sub in subsets.items():
                        positions=[ids.index(item) for item in sub]
                        mean,ci,boot=interval(values[positions],indices[name],run_indices)
                        row['scores'][name]={'accuracy':mean,'ci95':ci,'items':len(sub),'operational_runs':len(seeds),'item_only_ci95':interval(values[positions],indices[name])[1]}
                    row['diagnostics']={}
                    for metric in next(iter(metrics.values())):
                        if metric=='correct':continue
                        val=np.array([[metrics[(spec['model'],quant,arm,seed,item)][metric] for seed in seeds] for item in ids])
                        mean,ci,unused=interval(val,indices['all'],run_indices)
                        row['diagnostics'][metric]={'rate':mean,'ci95':ci}
                else:
                    row['scores']=None;row['reason']='Incomplete cell: no full-design CI or fabricated missing outputs'
                tables.append(row)
        for subset in ('all','required'):
            positions=[ids.index(item) for item in subsets[subset]]
            effects={}
            for arm in arms[1:]:
                needed=[('F16','free'),('Q4_K_M','free'),('F16',arm),('Q4_K_M',arm)]
                if not all(x in arrays for x in needed):continue
                free=arrays['F16','free'][positions]-arrays['Q4_K_M','free'][positions]
                constrained=arrays['F16',arm][positions]-arrays['Q4_K_M',arm][positions]
                net=free-constrained
                fm,fci,fb=interval(free,indices[subset],run_indices);cm,cci,cb=interval(constrained,indices[subset],run_indices);nm,nci,nb=interval(net,indices[subset],run_indices)
                effect={'model':spec['model'],'subset':subset,'decoder':arm,'free_loss':fm,'free_loss_ci95':fci,
                        'constrained_loss':cm,'constrained_loss_ci95':cci,'net_recovery':nm,'net_recovery_ci95':nci,
                        'recovery_share':nm/fm if fm>0 else None,
                        'recovery_share_reason':None if fm>0 else 'Nonpositive observed free loss; ratio undefined',
                        'recovery_share_ci95':[float(x) for x in np.quantile(nb/fb,[.025,.975])] if np.all(fb>0) else None,
                        'ratio_denominator_stable':bool(np.all(fb>0))}
                effects[arm]=net;recoveries.append(effect)
            for alternative in ('loose','trigger_strict'):
                if 'whole_strict' in effects and alternative in effects:
                    mean,ci,unused=interval(effects['whole_strict']-effects[alternative],indices[subset],run_indices)
                    contrasts.append({'model':spec['model'],'subset':subset,'contrast':'whole_strict minus '+alternative,
                                      'incremental_recovery_difference':mean,'ci95':ci})
    result={'created_at':now(),'run_id':args.run_id,'observations':len(rows),'expected_observations':24000,
            'inference_settings':{k:protocol[k] for k in ('temperature','parallel_slots','context_per_slot','max_output_tokens','cache_type_k','cache_type_v')},
            'complete':len(rows)==24000 and all(t['complete'] for t in tables),
            'bootstrap':{'unit':'crossed original-item and operational-run resampling; shared draws across all conditions/models','replicates':reps,
                         'seed':protocol['execution']['bootstrap_seed'],'interval':'paired percentile 95%; unadjusted exploratory intervals',
                         'same_indices_used_across_conditions':True,'item_only_sensitivity_included':True},
            'scores':tables,'recovery_effects':recoveries,'paired_decoder_contrasts':contrasts,'timing_events':timings}
    write_json(base/'summary.json',result)
    with (base/'diagnostics.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['model','precision','decoder','metric','rate','ci95_low','ci95_high','denominator_attempts'])
        for row in tables:
            if not row['complete']:continue
            for name,value in row['diagnostics'].items():
                writer.writerow([row['model'],row['precision'],row['decoder'],name,value['rate'],*value['ci95'],row['observed_attempts']])
    lines=['# Full-run scores and paired confidence intervals','',f"{len(rows)}/24000 observations; complete: {result['complete']}.",'',
           f"Each complete cell contains {len(ids)} original items × {len(seeds)} operational runs. The primary required-call endpoint contains {len(subsets['required'])} original items; repeated schedules are not independent new questions.",'',
           '| Model | Precision | Decoder | Observed / planned | All-case accuracy [95% CI] | Required-call accuracy [95% CI] |',
           '| --- | --- | --- | ---: | --- | --- |']
    for t in tables:
        def fmt(sub):
            if not t['complete']:return 'incomplete'
            v=t['scores'][sub];return f"{100*v['accuracy']:.1f}% [{100*v['ci95'][0]:.1f}, {100*v['ci95'][1]:.1f}]"
        lines.append(f"| {t['model']} | {t['precision']} | {t['decoder']} | {t['observed_attempts']}/{t['expected_attempts']} | {fmt('all')} | {fmt('required')} |")
    lines+=['','Primary intervals use crossed paired resampling of original items and five operational runs, retaining all conditions/models together. Item-only intervals are also saved as a sensitivity check; neither treats repeated schedules as independent items. Required-call subset is the prespecified primary endpoint; all cases include irrelevance. Status counts, category scores, deterministic diagnostic rates, signed precision losses, net recovery and paired decoder contrasts are in summary.json. A recovery share with nonpositive or unstable free loss is undefined or explicitly flagged; it is not a causal fraction of purely syntactic damage.','']
    (base/'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps({'observations':len(rows),'complete':result['complete'],'report':str(base/'REPORT.md')},indent=2))


if __name__=='__main__':main()
