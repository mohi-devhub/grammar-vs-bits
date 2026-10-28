"""Combine measured pilot throughput with explicit full-study cost assumptions."""
import argparse
import json
from pathlib import Path
from qunti.common import ROOT, now, write_json


def money(value):
    return "unavailable" if value is None else f"{value:.4f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-id', required=True)
    args = parser.parse_args()
    folder = ROOT / 'results/pilot' / args.batch_id
    summary = json.loads((folder / 'summary.json').read_text())
    billing = json.loads((ROOT / 'results/ops/project_billing.json').read_text())
    ledger = json.loads((ROOT / 'results/budget_ledger.json').read_text())
    batch = next(b for b in ledger['batches'] if b['id'] == args.batch_id)
    generations = summary['responses_received']
    app_cost = billing['app_costs_usd'].get(batch.get('app_id'))
    total = billing['observed_project_cost_usd']
    report = {'created_at': now(), 'batch': args.batch_id, 'gpu_type': summary['gpu_type'],
              'billing_capture': billing['captured_at'], 'project_cap_usd': ledger['october_cap_usd'],
              'reported_project_cost_usd': float(total) if total is not None else None,
              'reported_batch_cost_usd': float(app_cost) if app_cost is not None else None,
              'reported_batch_cost_per_received_generation_usd': float(app_cost) / generations if app_cost is not None and generations else None,
              'reported_project_cost_amortized_per_received_generation_usd': float(total) / generations if total is not None and generations else None,
              'billing_is_final': False, 'storage_completeness_established': False,
              'retained_reservations_usd': sum(b['reservation_usd'] for b in ledger['batches']),
              'full_run_approved': False}
    if summary.get('calibration_usable'):
        base = summary['projection']['qwen_main_8000_calls_resource_usd_at_observed_throughput']
        # Factors and allowance are transparent planning choices, not measurements.
        scenarios = []
        for m1, m3 in ((1, 1), (2, 6), (3, 10)):
            for arms in (1, 2):
                inference = base * (1 + m1 + m3) * arms
                scenarios.append({'assumed_llama_1b_cost_multiple': m1,
                                  'assumed_llama_3b_cost_multiple': m3,
                                  'assumed_four_arm_pool_cost_multiplier': arms,
                                  'inference_resource_usd': inference,
                                  'unmeasured_preparation_startup_storage_allowance_usd': 1.0,
                                  'additional_full_run_planning_usd': inference + 1.0,
                                  'project_total_at_reported_spend_usd': inference + 1.0 + float(total) if total is not None else None,
                                  'fits_cap_at_reported_spend': inference + 1.0 + float(total) <= ledger['october_cap_usd'] if total is not None else None})
        report['scenarios'] = scenarios
        report['forecast_scope'] = 'Same allocated GPU type as pilot. Model/arm factors and $1 setup/storage allowance are assumptions, not measured bounds. Prior reported spending may lag.'
        report['complete_run_unit'] = 'One model and operational seed, both precisions and all four arms on 200 frozen items: 1600 attempts, same GPU type'
        report['split_policy'] = 'If confirmed October headroom cannot cover all unchanged cells, allocate complete run units to October and the remainder to November from Nov 1; both require explicit approval.'
    else:
        report['forecast_unavailable_reason'] = 'No complete operationally usable pilot; do not extrapolate failures as throughput.'
    write_json(folder / 'budget_forecast.json', report)
    lines = ['# Pilot cost and full-run forecast', '', f"Batch {args.batch_id}; actual GPU type: {summary['gpu_type']}.", '',
             f"Returned generations: {generations}. Reported gross batch cost: {app_cost}; reported gross project cost to date: {total} USD.", '',
             'Reported amounts may lag and do not establish storage completeness. Credits offsetting the cash invoice do not erase these costs.', '']
    if generations:
        lines += [f"Reported batch cost per returned generation: {report['reported_batch_cost_per_received_generation_usd']!r} USD. "
                  f"Project cost to date amortized across these generations: {report['reported_project_cost_amortized_per_received_generation_usd']!r} USD. "
                  'These are reported-to-date ratios, not settled all-in unit costs. See summary.json for measured timing-based resource estimates.', '']
    if 'scenarios' in report:
        lines += ['| Assumed Llama 1B / 3B cost relative to Qwen | Assumed arm-pool factor | Additional full-run USD incl. $1 allowance | Project total at reported spend | Fits $12 at reported spend? |',
                  '| --- | ---: | ---: | ---: | --- |']
        for x in report['scenarios']:
            lines.append(f"| {x['assumed_llama_1b_cost_multiple']} / {x['assumed_llama_3b_cost_multiple']} | {x['assumed_four_arm_pool_cost_multiplier']} | "
                         f"{money(x['additional_full_run_planning_usd'])} | {money(x['project_total_at_reported_spend_usd'])} | {x['fits_cap_at_reported_spend']} |")
        lines += ['', report['forecast_scope'], '', report['split_policy'], '',
                  'Do not reduce arms, seeds, cases or models to fit. Reservations are held funds, not measured spending. Reconcile lagging charges and outstanding reserves before approving another batch; ask before any projected batch over $5.', '']
    else:
        lines += [report['forecast_unavailable_reason'], '']
    lines += ['The full run remains unlaunched and requires the researcher’s explicit OK. Direction 2 remains the planned follow-up.', '']
    (folder / 'budget_forecast.md').write_text('\n'.join(lines))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
