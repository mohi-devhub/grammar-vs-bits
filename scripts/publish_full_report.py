"""Publish local documentation from complete saved results, never from forecasts."""
import argparse
import json
import re
from qunti.common import ROOT,now,write_json
from scripts.presentation import headline,precision_comparison


def pct(value,ci):
    return f'{100*value:.1f}% [{100*ci[0]:.1f}, {100*ci[1]:.1f}]'


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);args=p.parse_args()
    folder=ROOT/'results/full'/args.run_id
    summary=json.loads((folder/'summary.json').read_text());cost=json.loads((folder/'costs.json').read_text())
    optional_path=ROOT/'results/sensitivity/pythonic-002/summary.json'
    optional=json.loads(optional_path.read_text()) if optional_path.exists() else None
    if not summary['complete']:raise RuntimeError('Do not publish incomplete data as the full experiment')
    integrity=json.loads((folder/'integrity.json').read_text())
    lines=['# Full-study report','',f"The matrix frozen before execution is complete: {summary['observations']:,}/{summary['expected_observations']:,} observations. All original items, decoder arms, precisions and operational runs are retained.",'',
           f'[All model × precision × decoder scores and CIs](../results/full/{args.run_id}/REPORT.md), [raw/scored result summary](../results/full/{args.run_id}/summary.json), [cost accounting](../results/full/{args.run_id}/COSTS.md), [integrity checks](../results/full/{args.run_id}/integrity.json).','',
           '| Model | Q4 free accuracy [95% CI] | Q4 whole-strict accuracy [95% CI] | Incremental recovery [95% CI], points | Share interpretation |','| --- | --- | --- | --- | --- |']
    findings=[]
    for model in integrity['models']:
        effect=next(r for r in summary['recovery_effects'] if r['model']==model['model'] and r['subset']=='required' and r['decoder']=='whole_strict')
        share='Undefined: nonpositive observed free loss' if effect['recovery_share'] is None else 'Unstable denominator; no share CI' if not effect['ratio_denominator_stable'] else pct(effect['recovery_share'],effect['recovery_share_ci95'])
        effect_text=pct(effect['net_recovery'],effect['net_recovery_ci95']).replace('%',' percentage points',1)
        cells={r['decoder']:r for r in summary['scores'] if r['model']==model['model'] and r['precision']=='Q4_K_M'}
        free=cells['free']['scores']['required'];strict=cells['whole_strict']['scores']['required']
        lines.append(f"| {model['model']} | {pct(free['accuracy'],free['ci95'])} | {pct(strict['accuracy'],strict['ci95'])} | {effect_text} | {share} |")
        parallel=cells['whole_strict']['scores']['parallel']
        findings.append(f"{model['model']}: Q4 required-call accuracy changes from {pct(free['accuracy'],free['ci95'])} with free decoding to {pct(strict['accuracy'],strict['ci95'])} with whole strict. Whole-strict incremental recovery is {effect_text}. {share}. Q4 whole-strict parallel-call accuracy is {pct(parallel['accuracy'],parallel['ci95'])}; a valid single call can still fail a task requiring several calls.")
    lo,hi=cost['pilot_forecast_total_range_usd']
    lines+=['',f"The primary campaign snapshot at {cost['captured_at']} reports gross project cost ${cost['reported_project_cost_usd']:.6f}, against the ${cost['cap_usd']:.2f} cap, before the separately approved Pythonic follow-up. The original pilot planning range was ${lo:.2f}–${hi:.2f}. Metering can lag; storage completeness is not established. All earlier setup failures and interrupted collections remain in the cost record.",'',
            'Intervals use crossed paired resampling of original items and operational-run labels. Item-only sensitivity intervals, category endpoints, overlapping diagnostic flags, operational failures and paired decoder contrasts are released. They are pointwise, unadjusted intervals. A positive constrained gain is not a causal partition of syntax and meaning.','',
            'The allocation selector stayed A10; the exact device-reported names are retained per item. Within a model, all conditions in the primary matrix share its worker session. Interrupted collections were retained separately and never pooled into the primary comparison. Direction 2 remains planned and unevaluated.','']
    shutdown=ROOT/'results/ops'/f'{args.run_id}_final_shutdown.json'
    sensitivity=folder/'failure_sensitivity.json'
    if sensitivity.exists():
        check=json.loads(sensitivity.read_text())
        changes=sum(r['interval_interpretation_changed'] for r in check['recovery_effects'])
        lines += [f"[Failure breakdown and post-hoc exclusion checks](../results/full/{args.run_id}/FAILURE_SENSITIVITY.md) report all cells and three exclusion rules. Directional interval classifications change in {changes} recovery effects across those rules and both endpoints. These checks condition on completion and leave the primary results frozen before execution unchanged.",'']
    if shutdown.exists():
        status=json.loads(shutdown.read_text())
        lines += [f"At {status['captured_at']}, the shutdown snapshot records {len(status['own_apps_active'])} active project apps and {len(status['own_containers_active'])} active project containers. Other authorized projects were preserved. [Shutdown evidence](../results/ops/{shutdown.name}).",'']
    optional_learning=''
    if optional and optional['complete']:
        lines += ['## Separate Pythonic format sensitivity','',
                  '[All additional scores, protocol contrasts and precision interactions](../results/sensitivity/pythonic-002/REPORT.md). These outputs are not pooled into the primary matrix.','',
                  '| Model | Q4 whole-strict parallel accuracy, JSON → Pythonic | Paired protocol gain [95% CI], points |',
                  '| --- | --- | --- |']
        for model in optional['models']:
            row=next(r for r in optional['scores'] if (r['model'],r['precision'],r['decoder'],r['subset'])==(model,'Q4_K_M','whole_strict','parallel'))
            contrast=next(r for r in optional['protocol_contrasts'] if (r['model'],r['precision'],r['decoder'])==(model,'Q4_K_M','whole_strict'))
            values=f"{100*row['primary_json_accuracy']:.1f}% → {pct(row['accuracy'],row['ci95'])}"
            lines.append(f"| {model} | {values} | {pct(contrast['gain_pythonic_minus_json'],contrast['ci95']).replace('%','',1)} |")
            optional_learning+=f"\n\n{model}: on the same parallel questions, Q4 whole-strict accuracy changes from {100*row['primary_json_accuracy']:.1f}% under the original JSON contract to {pct(row['accuracy'],row['ci95'])} under the Pythonic contract. This changes the serving contract as a whole, rather than isolating a parser-only effect."
        optional_learning+='\n\nLow parallel scores in the original JSON setup should not be treated as an intrinsic limitation of these Llama models. The separate report gives the matched protocol contrasts and their intervals. The original accuracy numbers and their precision interaction remain facts about the original contract.\n'
        lines += ['',optional_learning.strip(),'',f"Additional reported app costs, including the failed setup: {optional['costs']['optional_reported_usd']} USD. Latest reported project total: {optional['costs']['project_reported_usd']} USD. Caps remain $3 additional and $12 total; metering may lag.",'']
    (ROOT/'docs/FULL_REPORT.md').write_text('\n'.join(lines))
    def generated_section(path,text):
        data=path.read_text();marker='<!-- generated-full-result -->';end='<!-- /generated-full-result -->'
        block=marker+'\n'+text+'\n'+end
        if marker in data and end in data:data=re.sub(re.escape(marker)+'.*?'+re.escape(end),lambda m:block,data,flags=re.S)
        else:data+='\n'+block+'\n'
        path.write_text(data)
    budget=f"\n## Completed full study\n\nReported gross project cost: ${cost['reported_project_cost_usd']:.6f}; cap ${cost['cap_usd']:.2f}; pilot planning range ${lo:.2f}–${hi:.2f}. This snapshot is not a settled invoice. Full per-model forecasts, timings, attribution and denominators are in results/full/{args.run_id}/costs.json. Earlier failed attempts remain charged to the project.\n\n"
    budget+='| Batch | Recorded forecast USD | Retained hold USD | Reported USD | State |\n| --- | ---: | ---: | ---: | --- |\n'
    for batch in cost['all_project_batches']:
        forecast='not recorded' if batch['projection_usd'] is None else f"{batch['projection_usd']:.4f}"
        reported='unknown / no row' if batch['reported_to_date_usd'] is None else f"{batch['reported_to_date_usd']:.6f}"
        budget+=f"| {batch['batch_id']} | {forecast} | {batch['retained_hold_usd']:.4f} | {reported} | {batch['status']} |\n"
    budget+='\nHolds are allowances, not measured charges. Missing metering rows remain unknown. Project-level storage and other unattributed rows are included in the project total without being invented as per-batch charges.\n'
    generated_section(ROOT/'BUDGET.md',budget)
    exclusion_note=''
    if sensitivity.exists():
        exclusion_note='\n\nThe later exclusion checks use saved answers only. Removing an incomplete answer from just one condition changes the comparison population. To preserve pairing, the matched check removes its corresponding answers from every condition of that model/item/run. A stricter check removes the entire item across runs too. These checks select on whether generation finished, so they can favor easier questions and cannot tell us what a longer generation would have answered. Full denominators and intervals are in results/full/'+args.run_id+'/FAILURE_SENSITIVITY.md.\n'
    generated_section(ROOT/'LEARNING.md','\n## What the completed full study means\n\n'+'\n\n'.join(findings)+'\n\nThese compare the F16-to-Q4 accuracy gap with and without whole-response constraints. They subtract the benefit constraints already have at F16. Negative incremental recovery means the decoder helped F16 more, or harmed it less; it does not by itself mean constraints lowered Q4 accuracy. A confidence interval spanning zero does not establish the direction of recovery. Valid structure still does not guarantee a correct tool choice or value; the released diagnostics show both. Five repeated greedy schedules remain paired with their original questions, rather than being counted as new questions.\n'+exclusion_note+optional_learning)
    readme=ROOT/'README.md'
    previous=ROOT/'.cache/README-before-final.md'
    if not previous.exists():previous.write_text(readme.read_text())
    text=(ROOT/'docs/README_TEMPLATE.md').read_text()
    display_cost=optional['costs']['project_reported_usd'] if optional else cost['reported_project_cost_usd']
    for key,value in {'observations':f"{summary['observations']:,}",'run_id':args.run_id,'reported_cost':f"{display_cost:.6f}"}.items():
        text=text.replace('{{'+key+'}}',value)
    if optional:
        text=text.replace('{{format_finding}}',headline(optional,intervals=True)).replace('{{precision_comparison}}',precision_comparison(optional))
    if '{{' in text:raise RuntimeError('Unfilled public documentation field')
    readme.write_text(text)
    if optional:
        with readme.open('a') as stream:
            stream.write('\nThe additional Pythonic format sensitivity is complete and reported separately in [its report](results/sensitivity/pythonic-002/REPORT.md). It does not replace the primary matrix.\n')
        note=f"\n## Completed Pythonic format follow-up\n\nAdditional app metering reported to date: {optional['costs']['optional_reported_usd']} USD, including the zero-generation setup failure. Latest project reported total: {optional['costs']['project_reported_usd']} USD; caps $3 additional/$12 project. This is not a settled invoice.\n\n"
        note+='| Batch | Reported USD |\n| --- | ---: |\n'
        for row in optional['costs']['batches']:
            value='unknown / no row' if row['reported_usd'] is None else str(row['reported_usd'])
            note+=f"| {row['batch_id']} | {value} |\n"
        data=(ROOT/'BUDGET.md').read_text();marker='<!-- generated-pythonic-cost -->';end='<!-- /generated-pythonic-cost -->'
        block=marker+'\n'+note+'\n'+end
        data=re.sub(re.escape(marker)+'.*?'+re.escape(end),lambda m:block,data,flags=re.S) if marker in data else data+'\n'+block+'\n'
        (ROOT/'BUDGET.md').write_text(data)
    directions=ROOT/'docs/DIRECTIONS.md';text=directions.read_text()
    if text.startswith(('**Execution status updated ','**Completed execution:**')):text=text.split('\n\n',1)[1]
    directions.write_text(f"**Completed execution:** Direction 1 finished its unchanged {summary['observations']:,}-observation matrix frozen before execution. Direction 2 remains the planned follow-up and was not evaluated. The dated audit below preserves the earlier choice and approval history.\n\n"+text)
    learning=ROOT/'LEARNING.md';text=learning.read_text().replace('Full-study findings are not available.','The completed full-study findings are in docs/FULL_REPORT.md and the generated section below.');learning.write_text(text)
    write_json(folder/'documentation_build.json',{'created_at':now(),'run_id':args.run_id,'sources':['summary.json','costs.json','integrity.json'],'generated_report':'docs/FULL_REPORT.md'})
    print('Published local full-result documentation from saved measurements.')


if __name__=='__main__':main()
