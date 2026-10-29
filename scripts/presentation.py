"""Result-derived wording shared by the manuscript and public documentation."""


def contract_rows(summary):
    rows=[]
    for model in summary['models']:
        def cell(precision):
            return next(r for r in summary['scores'] if (r['model'],r['precision'],r['decoder'],r['subset'])==(model,precision,'whole_strict','parallel'))
        low=cell('Q4_K_M');high=cell('F16')
        gain=next(r for r in summary['protocol_contrasts'] if (r['model'],r['precision'],r['decoder'])==(model,'Q4_K_M','whole_strict'))
        rows.append({'model':model,'label':'1B' if '-1B-' in model else '3B','items':low['items'],
                     'json':low['primary_json_accuracy'],'pythonic':low['accuracy'],'pythonic_ci95':low['ci95'],
                     'gain':gain['gain_pythonic_minus_json'],'gain_ci95':gain['ci95'],
                     'pythonic_precision_gap':high['accuracy']-low['accuracy']})
    return rows


def headline(summary,intervals=False):
    parts=[]
    for row in contract_rows(summary):
        text=f"Llama-{row['label']} Q4 whole-strict parallel accuracy rises from {100*row['json']:.1f}% to {100*row['pythonic']:.1f}%"
        if intervals:
            lo,hi=row['gain_ci95'];text+=f" (paired gain {100*row['gain']:.1f} [{100*lo:.1f}, {100*hi:.1f}] points)"
        parts.append(text)
    return '; '.join(parts)+'.'


def precision_comparison(summary):
    rows=contract_rows(summary)
    gaps=' and '.join(f"{100*r['pythonic_precision_gap']:.1f}" for r in rows)
    gains=' and '.join(f"{100*r['gain']:.1f}" for r in rows)
    return f'The observed format-contract gains of {gains} points are much larger than the corresponding Pythonic F16-to-Q4 whole-strict gaps of {gaps} points.'


def recovery_statement(summary):
    paired=[r for r in summary['recovery_effects'] if r['subset']=='parallel']
    if all(r['ci95'][0]<=0<=r['ci95'][1] and r['protocol_recovery_difference_ci95'][0]<=0<=r['protocol_recovery_difference_ci95'][1] for r in paired):
        return 'Sensitivity parallel incremental recovery and its protocol change remain inconclusive.'
    return 'The released paired intervals describe sensitivity incremental recovery and its protocol change.'


def failure_rows(summary):
    return [{'model':model,'label':'1B' if '-1B-' in model else '3B',
             'cells':[next(r for r in summary['status_breakdown'] if (r['model'],r['precision'],r['decoder'])==(model,q,a))
                      for q in ['F16','Q4_K_M'] for a in ['free','whole_strict']]}
            for model in summary['models']]


def failure_table_tex(summary):
    lines=[r'\begin{center}\footnotesize',r'\begin{tabular}{lrrrr}\toprule',
           r' & \multicolumn{2}{c}{F16} & \multicolumn{2}{c}{Q4\_K\_M} \\',
           r'Llama & Free & Whole strict & Free & Whole strict \\\midrule']
    for row in failure_rows(summary):
        lines.append(row['label']+' & '+' & '.join(str(cell['statuses'].get('token_limit',0)) for cell in row['cells'])+r' \\')
    lines += [r'\bottomrule\end{tabular}\end{center}']
    count=summary['status_counts']['token_limit']
    per_cell={cell['observations'] for row in failure_rows(summary) for cell in row['cells']}
    assert len(per_cell)==1
    return (r'\paragraph{Sensitivity token limits.} '+f'The {count} token-limit outcomes fall as follows; each cell has {next(iter(per_cell))} observations.\n'
            +'\n'.join(lines)+'\nAll limits already count as incorrect in the reported accuracies and intervals. The large failure-inclusive contract gains therefore remain. '+recovery_statement(summary)+' Conclusions concern the fixed output cap, not unlimited generation. No added exclusion analysis is claimed.')
