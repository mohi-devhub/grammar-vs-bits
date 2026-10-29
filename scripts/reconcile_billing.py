"""Summarize one saved tagged billing snapshot; never infer missing cost as zero."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
from qunti.common import ROOT, now, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.snapshot.read_text())
    own = []
    for row in rows:
        tags = row.get('tags') or {}
        if isinstance(tags, str):
            tags = json.loads(tags)
        if tags.get('project') in ('grammar-vs-bits','qunti-check') or row.get('description') in ('grammar-vs-bits-pilot', 'grammar-vs-bits-artifacts', 'qunti-check-pilot', 'qunti-check-artifacts'):
            own.append(row)
    app_costs = {}
    for row in own:
        key = row['object_id']
        app_costs[key] = app_costs.get(key, Decimal(0)) + Decimal(row['cost'])
    path = ROOT / 'results/budget_ledger.json'
    ledger = json.loads(path.read_text())
    for batch in ledger['batches']:
        app_id = batch.get('app_id')
        app_file = ROOT / f'results/ops/{batch["id"]}_app.json'
        if not app_id and app_file.exists():
            app_id = json.loads(app_file.read_text())['app_id']
            batch['app_id'] = app_id
        batch['metered_to_date_usd'] = str(app_costs[app_id]) if app_id in app_costs else None
        batch['metering_is_final'] = False
        # Keep reservations in place: report lag and absent rows cannot release them.
    write_json(path, ledger)
    report = {'captured_at': now(), 'snapshot': str(args.snapshot),
              'scope': 'Gross project-tagged/resource-named costs reported in this snapshot; may lag; not a settled invoice. Storage completeness not established.',
              'observed_project_cost_usd': str(sum(app_costs.values(), Decimal(0))) if own else None,
              'app_costs_usd': {k: str(v) for k, v in app_costs.items()}, 'rows': own,
              'missing_rows_are_not_zero_cost': True,
              'reservations_retained_usd': sum(b['reservation_usd'] for b in ledger['batches'])}
    write_json(ROOT / 'results/ops/project_billing.json', report)
    print(json.dumps({k:v for k,v in report.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
