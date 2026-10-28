"""Capture attributed gross metering and compare it with the saved pilot forecast."""
import argparse
import json
from qunti.common import ROOT, now, write_json
from scripts.full_run import billing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    folder = ROOT / 'results/full' / args.run_id
    state = json.loads((folder / 'state.json').read_text())
    total, by_app = billing(args.run_id + '_final')
    if total<=0 and state['historical_reported_cost_usd']>0:
        raise RuntimeError('No positive project metering was returned despite known prior spend; preserve the existing cost record rather than report zero')
    forecast = json.loads((ROOT / 'results/pilot/pilot-008/budget_forecast.json').read_text())
    scenarios = [s for s in forecast['scenarios'] if (s['assumed_llama_1b_cost_multiple'], s['assumed_llama_3b_cost_multiple']) == (2, 6)]
    models = []
    for row in state['model_sessions']:
        value = by_app.get(row['app_id'])
        gate = json.loads((ROOT / f"results/ops/{args.run_id}_{row['model'].split('/')[-1]}_budget_gate.json").read_text())
        models.append({**row, 'reported_model_cost_usd': value,
                       'reported_model_cost_per_attempt_usd': value / row['attempted'] if value is not None and row['attempted'] else None,
                       'pre_model_projection_usd': gate['next_model_projection_usd']})
    observations = sum(r['attempted'] for r in models)
    reported_run = sum(r['reported_model_cost_usd'] for r in models) if all(r['reported_model_cost_usd'] is not None for r in models) else None
    ledger=json.loads((ROOT/'results/budget_ledger.json').read_text())
    batches=[]
    for batch in ledger['batches']:
        app_id=batch.get('app_id')
        info=ROOT/f"results/ops/{batch['id']}_app.json"
        if not app_id and info.exists():app_id=json.loads(info.read_text()).get('app_id')
        batches.append({'batch_id':batch['id'],'app_id':app_id,'status':batch['status'],
                        'projection_usd':batch.get('projected_cost_usd'),'retained_hold_usd':batch['reservation_usd'],
                        'reported_to_date_usd':by_app.get(app_id)})
    result = {'captured_at': now(), 'run_id': args.run_id, 'billing_snapshot': f'results/ops/{args.run_id}_final_billing.json',
              'scope': 'Gross project-tagged/resource-named metering reported to date; includes setup and aborted attempts. Storage completeness is not established. This is not a settled invoice.',
              'reported_project_cost_usd': total, 'design_complete':bool(state.get('complete')),
              'reported_registered_session_cost_usd': reported_run,
              'registered_session_observations': observations,
              'reported_registered_session_cost_per_observation_usd': reported_run / observations if reported_run is not None and observations else None,
              'reported_project_cost_amortized_per_registered_observation_usd': total / observations if observations else None,
              'cap_usd': state['cap_usd'], 'reported_headroom_usd': state['cap_usd'] - total,
              'pilot_forecast_total_range_usd': [min(s['project_total_at_reported_spend_usd'] for s in scenarios), max(s['project_total_at_reported_spend_usd'] for s in scenarios)],
              'forecast_source': 'results/pilot/pilot-008/budget_forecast.json', 'models': models,
              'all_project_batches':batches,
              'failed_model_attempts': [{**r,'reported_model_cost_usd':by_app.get(r.get('app_id'))} for r in state.get('failed_model_attempts',[])],
              'metering_is_final': False, 'missing_rows_are_not_zero_cost': True}
    write_json(folder / 'costs.json', result)
    lines = ['# Actual reported cost versus forecast', '',
             f"Gross project cost reported to date: ${total:.6f}, against ${state['cap_usd']:.2f} cap. This includes earlier failures and the interrupted collection. Metering can lag; storage completeness is unresolved.", '',
             '| Model | Attempts | Next-model forecast USD | Reported model USD | Reported USD / attempt |',
             '| --- | ---: | ---: | ---: | ---: |']
    if not state.get('complete'):
        lines.insert(2,'The registered design is incomplete. There is no measured full-matrix cost; current metering and the complete-study forecast concern different workloads.\n')
    for row in models:
        value = row['reported_model_cost_usd']
        cost_text = f'{value:.6f}' if value is not None else 'not reported'
        per = row['reported_model_cost_per_attempt_usd']
        per_text = f'{per:.8f}' if per is not None else 'not reported'
        lines.append(f"| {row['model']} | {row['attempted']} | {row['pre_model_projection_usd']:.4f} | {cost_text} | {per_text} |")
    lower, upper = result['pilot_forecast_total_range_usd']
    lines += ['', f'Pilot project-total planning range: ${lower:.2f}–${upper:.2f}. Model multipliers and setup/storage allowance were assumptions, not measured bounds.', '',
              'Model reported costs include billed setup/serving resources attributed to that app; they do not include historical apps. Timed body costs and conservative model bounds are retained in costs.json. Generation denominators are attempts, including incomplete or failed responses; the primary matrix is never shrunk to successful calls.']
    (folder / 'COSTS.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'models'}, indent=2))


if __name__ == '__main__':
    main()
