"""Exploratory paired outcomes and observable failure rescues; no causal labels."""
import argparse
import json
import numpy as np
from qunti.common import ROOT, read_jsonl, write_json, now
from scripts.report_full import interval


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    folder = ROOT / 'results/full' / args.run_id
    summary = json.loads((folder / 'summary.json').read_text())
    protocol = json.loads((ROOT / 'configs/protocol.json').read_text())
    if not summary['complete']:
        raise RuntimeError('Transition analysis requires the complete matrix')
    rows = read_jsonl(folder / 'scored.jsonl')
    lookup = {(r['model'], r['quant'], r['condition'], r['id'], r['seed']): r for r in rows}
    specs = json.loads((ROOT / 'configs/full_models.json').read_text())
    items = read_jsonl(ROOT / 'data/frozen.jsonl')
    rng = np.random.default_rng(protocol['execution']['bootstrap_seed'])
    out = []
    for subset in ['all', 'required']:
        ids = [r['id'] for r in items if subset == 'all' or r['category'] != 'irrelevance']
        indices = rng.integers(0, len(ids), (protocol['execution']['bootstrap_replicates'], len(ids)))
        runs = rng.integers(0, len(protocol['run_seeds']), (len(indices), len(protocol['run_seeds'])))
        for spec in specs:
            for q in protocol['precisions']:
                for arm in protocol['arms'][1:]:
                    values = {k: np.zeros((len(ids), len(protocol['run_seeds']))) for k in
                              ['both_correct', 'free_only_correct', 'decoder_only_correct', 'both_wrong',
                               'rescued_free_format_failure', 'rescued_free_schema_valid_failure',
                               'remaining_decoder_schema_valid_failure']}
                    for i, item in enumerate(ids):
                        for j, seed in enumerate(protocol['run_seeds']):
                            f = lookup[spec['model'], q, 'free', item, seed]['score']
                            d = lookup[spec['model'], q, arm, item, seed]['score']
                            a, b = f['correct'], d['correct']
                            values['both_correct'][i, j] = a and b
                            values['free_only_correct'][i, j] = a and not b
                            values['decoder_only_correct'][i, j] = not a and b
                            values['both_wrong'][i, j] = not a and not b
                            values['rescued_free_format_failure'][i, j] = not a and f['invalid_json_or_format'] and b
                            values['rescued_free_schema_valid_failure'][i, j] = not a and f['schema_valid'] and b
                            values['remaining_decoder_schema_valid_failure'][i, j] = not b and d['schema_valid']
                    record = {'model': spec['model'], 'precision': q, 'decoder': arm, 'subset': subset, 'metrics': {}}
                    for name, array in values.items():
                        mean, ci, unused = interval(array, indices, runs)
                        record['metrics'][name] = {'attempts': int(array.sum()), 'denominator': array.size,
                                                   'rate': mean, 'ci95': ci}
                    out.append(record)
    write_json(folder / 'transitions.json', {'created_at': now(), 'run_id': args.run_id, 'exploratory': True,
               'interpretation': 'Paired observable outcomes. Rescue of a format failure is not proof of exclusively syntactic knowledge loss. Schema-valid failures are task failures, not direct evidence of a particular internal mechanism.',
               'rows': out})
    print('Saved exploratory paired transitions with crossed paired intervals.')


if __name__ == '__main__':
    main()
