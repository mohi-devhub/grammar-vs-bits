"""Generate manuscript numbers from completed, saved result artifacts only."""
import argparse
import json
from qunti.common import ROOT, write_json, now
from scripts.presentation import headline,precision_comparison,failure_table_tex,contract_rows,recovery_statement


def tex(value):
    return str(value).replace('_', r'\_').replace('%', r'\%').replace('&', r'\&')


def percent(value):
    return f'{100 * value:.1f}'


def estimate(value, interval):
    return f'{percent(value)} [{percent(interval[0])}, {percent(interval[1])}]'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    folder = ROOT / 'results/full' / args.run_id
    summary = json.loads((folder / 'summary.json').read_text())
    costs = json.loads((folder / 'costs.json').read_text())
    sensitivity = json.loads((folder / 'failure_sensitivity.json').read_text())
    optional=ROOT/'results/sensitivity/pythonic-002/summary.json'
    followup=json.loads(optional.read_text())
    if not followup['complete']:raise RuntimeError('The reframed paper requires the complete saved sensitivity')
    import hashlib
    for name, expected in sensitivity['primary_files_sha256'].items():
        with (ROOT/name).open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=expected:
                raise RuntimeError('Rerun report_failure_sensitivity after changing primary result files')
    if not summary['complete']:
        raise RuntimeError('Results manuscript requires the complete matrix frozen before execution; no placeholders')
    integrity=json.loads((folder/'integrity.json').read_text())
    if not integrity['complete']:raise RuntimeError('Validate the actual complete matrix before generating paper numbers')
    specs = json.loads((ROOT / 'configs/full_models.json').read_text())
    output = ROOT / 'paper/generated'
    output.mkdir(exist_ok=True)
    def save(name, value):
        (output / (name + '.tex')).write_text(value + '\n')
    scores = summary['scores']
    def cell(model, quant, arm):
        return next(r for r in scores if (r['model'], r['precision'], r['decoder']) == (model, quant, arm))
    first = scores[0]['scores']
    categories = ['simple', 'multiple', 'parallel', 'irrelevance']
    setup = ('We evaluate ' + ', '.join(r'\texttt{' + tex(s['slug']) + '}' for s in specs)
             + '. The frozen sample contains ' + str(first['all']['items']) + ' original cases: '
             + ', '.join(str(first[c]['items']) + ' ' + c for c in categories)
             + '. The primary required-call subset contains ' + str(first['required']['items'])
             + ' items. Each precision--decoder cell has ' + str(first['all']['operational_runs'])
             + ' operational runs, totaling ' + f"{summary['observations']:,}"
             + ' benchmark generations in the complete matrix.')
    execution=summary['inference_settings']
    setup+=(' Decoding uses temperature '+str(execution['temperature'])+', '+str(execution['parallel_slots'])
            +' parallel server slots, a '+str(execution['context_per_slot'])+'-token input-plus-output budget per request, and an output cap of '
            +str(execution['max_output_tokens'])+' tokens.')
    save('setup', setup)
    save('macros', '% Generated from saved result artifacts; edit the generator, not these files.')
    names = {'free': 'Free', 'loose': 'Loose', 'trigger_strict': 'Triggered', 'whole_strict': 'Whole strict'}
    lines = [r'\begin{tabular}{llrrrr}', r'\toprule',
             r'Model & Precision & Free & Loose & Triggered & Whole strict \\', r'\midrule']
    for spec in specs:
        for quant in ['F16', 'Q4_K_M']:
            values = [cell(spec['model'], quant, arm)['scores']['required'] for arm in names]
            lines.append(tex(spec['slug'].replace('-Instruct', '')) + ' & ' + tex(quant) + ' & '
                         + ' & '.join(estimate(v['accuracy'], v['ci95']) for v in values) + r' \\')
    lines += [r'\bottomrule', r'\end{tabular}']
    save('accuracy_table', '\n'.join(lines))
    effects = [r for r in summary['recovery_effects'] if r['subset'] == 'required']
    text = []
    abstracts = []
    conclusions = []
    for spec in specs:
        paragraph=[]
        rows = [r for r in effects if r['model'] == spec['model']]
        whole = next(r for r in rows if r['decoder'] == 'whole_strict')
        free = cell(spec['model'], 'Q4_K_M', 'free')['scores']['required']
        strict = cell(spec['model'], 'Q4_K_M', 'whole_strict')['scores']['required']
        label = tex(spec['slug'].replace('-Instruct', ''))
        paragraph.append(label + ': Q4 required-call accuracy changes from '+percent(free['accuracy'])
                         +r'\% free to '+percent(strict['accuracy'])+r'\% whole strict. Its incremental recovery is '
                         +estimate(whole['net_recovery'],whole['net_recovery_ci95'])+' percentage points.')
        structural=cell(spec['model'],'Q4_K_M','whole_strict')['diagnostics']['schema_valid']
        all_score=cell(spec['model'],'Q4_K_M','whole_strict')['scores']['all']
        paragraph.append('Across all cases for '+label+', Q4 whole-strict response-structure validity is '
                    +estimate(structural['rate'],structural['ci95'])+r'\%, while official accuracy is '
                    +estimate(all_score['accuracy'],all_score['ci95'])+r'\%.')
        category_scores=cell(spec['model'],'Q4_K_M','whole_strict')['scores']
        if spec['family']=='llama':
            paragraph.append('Its Q4 whole-strict parallel accuracy under the declared JSON contract is '
                             +estimate(category_scores['parallel']['accuracy'],category_scores['parallel']['ci95'])+r"\%. This does not measure the publisher Pythonic call-list contract.")
        abstracts.append(label + ' has whole-strict incremental recovery of '
                         + estimate(whole['net_recovery'], whole['net_recovery_ci95']) + ' percentage points')
        lo, hi = whole['net_recovery_ci95']
        finding = ('positive' if lo > 0 else 'negative' if hi < 0 else 'not resolved from zero by its interval')
        conclusions.append(label + "'s observed whole-strict incremental recovery is " + finding + '.')
        text.append(' '.join(paragraph))
    status_counts = {}
    for row in scores:
        for status, count in row['status_counts'].items():
            status_counts[status] = status_counts.get(status, 0) + count
    status_text = '; '.join(tex(k) + ': ' + str(v) for k, v in sorted(status_counts.items()))
    save('abstract_results','On the same '+str(contract_rows(followup)[0]['items'])+' parallel cases in a separate sensitivity, '+headline(followup,intervals=True).replace('%',r'\%')+' '+precision_comparison(followup)
         +' This separate sensitivity changes the prompt, parser and grammar together; it is not a randomized crossover or a parser-only causal effect. '+recovery_statement(followup)+' Intervals are pointwise, unadjusted and specific to this setup. No primary free-decoding precision-loss interval excludes zero.')
    save('intro_finding','On the same '+str(contract_rows(followup)[0]['items'])+' parallel items, the separate sensitivity identifies the serving contract as the larger observed contrast. '
         +precision_comparison(followup)
         +' This is a joint prompt/parser/grammar comparison, not a general law about quantization or an intrinsic Llama limitation.')
    save('results_text', '\n\n'.join(text) + '\n\nGeneration status counts are ' + status_text
         + '. Negative incremental recovery does not mean constraints lowered Q4 accuracy: they helped F16 more in these cells. Valid structure includes no-call responses; task correctness and irrelevance are scored separately. Other diagnostic rates, category endpoints, item-only sensitivity intervals, paired decoder contrasts and raw responses are released with the result tables. Intervals crossing zero do not establish equivalence.')
    lines = [r'\begin{table*}[t]\centering\scriptsize',
             r'\caption{Required-call signed precision loss and incremental recovery, in percentage points [95\% CI]. The final column is the normalized share (\%) when its denominator is stable.}',
             r'\begin{tabular}{llrrrr}\toprule',
             r'Model & Decoder & Free loss & Constrained loss & Net recovery & Recovery share \\\midrule']
    for spec in specs:
        for row in [r for r in effects if r['model'] == spec['model']]:
            share=('undefined' if row['recovery_share'] is None else 'unstable' if row['recovery_share_ci95'] is None
                   else estimate(row['recovery_share'],row['recovery_share_ci95'])+r'\%')
            lines.append(tex(spec['slug'].replace('-Instruct', '')) + ' & ' + names[row['decoder']] + ' & '
                         + ' & '.join(estimate(row[k], row[k + '_ci95']) for k in ['free_loss', 'constrained_loss', 'net_recovery'])
                         + ' & '+share+r' \\')
    lines += [r'\bottomrule\end{tabular}\end{table*}']
    save('effect_table', '\n'.join(lines))
    save('cost', 'The pilot planning scenario for the primary campaign was \\$'
         + f"{costs['pilot_forecast_total_range_usd'][0]:.2f}" + '--\\$'
         + f"{costs['pilot_forecast_total_range_usd'][1]:.2f}"
         + '. Gross tagged project cost reported at the pre-follow-up snapshot is \\$'
         + f"{costs['reported_project_cost_usd']:.4f}"
         + ', including retained setup and interrupted attempts, against the \\$'
         + f"{costs['cap_usd']:.2f}" + ' cap. Metering is reported to date, not a settled invoice. '
         + 'All final app and container states are saved separately from the billing snapshot.')
    save('conclusion','The separate sensitivity shows that the tool-call format contract has a much larger observed accuracy contrast than weight precision in this setup. '
         +headline(followup).replace('%',r'\%')
         +' This changes the interpretation of the low primary Llama parallel scores, while leaving the primary matrix unchanged. The comparison changes prompt, parser and grammar together. '+recovery_statement(followup)+' The pointwise, unadjusted intervals do not establish recovered quantization damage. No primary free-decoding precision-loss interval excludes zero.')
    failure_text=[]
    for spec in specs:
        group=[r for r in sensitivity['failure_breakdown'] if r['model']==spec['model']]
        replays=sum(r['grammar_trigger_replay_error'] for r in group)
        failure_text.append(tex(spec['slug'].replace('-Instruct',''))+' has '
                            +str(sum(r['token_limit'] for r in group))+' token-limit outcomes and '
                            +str(replays)+(' replay error' if replays==1 else ' replay errors'))
    matched=[r for r in sensitivity['recovery_effects'] if r['method']=='matched_panel'
             and r['subset']=='required' and r['decoder']=='whole_strict']
    matched_text=[]
    for spec in specs:
        row=next(r for r in matched if r['model']==spec['model'])
        matched_text.append(tex(spec['slug'].replace('-Instruct',''))+' '
                            +estimate(row['net_recovery'],row['net_recovery_ci95']))
    changes=sum(r['interval_interpretation_changed'] for r in sensitivity['recovery_effects'])
    contrast_changes=sum(r['interval_interpretation_changed'] for r in sensitivity['decoder_contrasts'])
    save('failure_sensitivity', r'\paragraph{Primary failures and post-hoc exclusion.} '
         +'; '.join(failure_text)+'. Failures concentrate in particular decoder/task cells; exclusion cannot be assumed independent of treatment or difficulty. '
         +'The analysis frozen before execution counts them as incorrect. We additionally exclude failures within each cell, '
         +'exclude a model/item/run from all precision--decoder cells whenever any cell failed, and exclude whole items '
         +'with any failure across conditions/runs. The middle rule preserves a common observed cohort; its required-call '
         +'whole-strict recovery is '+ '; '.join(matched_text)+r' percentage points [95\% CI]. '
         +'Directional interval classifications change in '+str(changes)+' recovery effects and '
         +str(contrast_changes)+' decoder contrasts across all three rules and both endpoints. '
         +'Cell-only exclusion compares different completed populations; every exclusion selects on a post-treatment outcome '
         +'and can favor easier items. None identifies performance with unlimited generation or a repaired engine. '
         +'The released failure report includes every cell count, retained denominator and supplementary interval; primary results remain unchanged.')
    optional=ROOT/'results/sensitivity/pythonic-002/summary.json'
    if optional.exists():
        from scripts.report_pythonic import paper_text
        followup=json.loads(optional.read_text())
        save('pythonic_sensitivity',paper_text(followup))
        save('sensitivity_token_limits',failure_table_tex(followup))
        extra=followup['costs']
        if extra['optional_reported_usd'] is not None:
            with (output/'cost.tex').open('a') as stream:
                stream.write('The separate Pythonic sensitivity adds \\$'+f"{extra['optional_reported_usd']:.4f}"
                             +', including failed/interrupted apps, for latest reported project cost \\$'+f"{extra['project_reported_usd']:.4f}"
                             +' against the additional \\$'+f"{extra['optional_cap_usd']:.2f}"+' and total \\$'+f"{extra['project_cap_usd']:.2f}"+' caps.\n')
    else:
        save('pythonic_sensitivity','% Separate optional study has not yet produced a complete result.')
    sources=[folder/name for name in ('summary.json','costs.json','failure_sensitivity.json')]
    if optional.exists():sources.append(optional)
    write_json(output / 'provenance.json', {'created_at': now(), 'run_id': args.run_id,
               'sources': [str(path.relative_to(ROOT)) for path in sources],
               'source_sha256': {str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
               'generator': 'scripts/build_paper_data.py'})
    print('Generated manuscript inputs from complete saved results.')


if __name__ == '__main__':
    main()
