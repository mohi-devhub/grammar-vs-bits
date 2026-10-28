"""Offline post-hoc sensitivity to recorded operational failures."""
import argparse
from collections import Counter
import csv
import hashlib
import json

import numpy as np

from qunti.common import ROOT, now, read_jsonl, write_json

EXCLUDED = {'token_limit', 'grammar_trigger_replay_error'}
ROUND_OFF_TOLERANCE = 1e-12
METHODS = {
    'cell_completed': 'Exclude only failed generations; cell populations differ.',
    'matched_panel': 'Exclude all eight conditions of a model/item/run if any failed.',
    'complete_item': 'Exclude an original item from all conditions/runs if any failed.',
}


def masked_bootstrap(values, mask, indices, run_indices):
    """Resample original items and run labels, retaining the selected denominator."""
    values = np.asarray(values, dtype=float)
    mask = np.asarray(mask, dtype=bool)
    if values.shape != mask.shape or values.ndim != 2 or not mask.any():
        raise ValueError('Expected nonempty item/run values and an aligned eligibility mask')
    weights = np.stack([(run_indices == r).mean(axis=1) for r in range(values.shape[1])], axis=1)
    numerator = np.einsum('bir,br->b', (values * mask)[indices], weights)
    denominator = np.einsum('bir,br->b', mask[indices], weights)
    if np.any(denominator == 0):
        raise ValueError('A bootstrap sample has no eligible observations; do not silently discard it')
    return float(values[mask].mean()), numerator / denominator


def interpretation(ci):
    return ('positive' if ci[0] > ROUND_OFF_TOLERANCE
            else 'negative' if ci[1] < -ROUND_OFF_TOLERANCE else 'includes_zero')


def ci(boot):
    bounds = np.quantile(boot, [.025, .975])
    return np.where(np.abs(bounds) < ROUND_OFF_TOLERANCE, 0, bounds).tolist()


def formatted(value, bounds):
    return f'{100*value:.2f} [{100*bounds[0]:.2f}, {100*bounds[1]:.2f}]'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    folder = ROOT / 'results/full' / args.run_id
    source_paths = [folder/'summary.json', folder/'scored.jsonl']
    summary = json.loads(source_paths[0].read_text())
    if not summary['complete']:
        raise RuntimeError('Sensitivity requires the complete matrix frozen before execution')
    rows = read_jsonl(source_paths[1])
    protocol = json.loads((ROOT/'configs/protocol.json').read_text())
    specs = json.loads((ROOT/'configs/full_models.json').read_text())
    items = read_jsonl(ROOT/'data/frozen.jsonl')
    ids = [i['id'] for i in items]
    seeds, arms, precisions = protocol['run_seeds'], protocol['arms'], protocol['precisions']
    lookup = {(r['model'], r['quant'], r['condition'], r['id'], r['seed']): r for r in rows}
    if len(lookup) != len(rows):
        raise RuntimeError('Duplicate observations')
    breakdown, failures = [], []
    for spec in specs:
        for quant in precisions:
            for arm in arms:
                selected = [lookup[spec['model'], quant, arm, item, seed] for item in ids for seed in seeds]
                statuses = Counter(r['status'] for r in selected)
                if set(statuses) - EXCLUDED - {'ok'}:
                    raise RuntimeError('Unexpected operational status requires an explicit policy')
                bad = [r for r in selected if r['status'] in EXCLUDED]
                if any(r['completed'] or r['score']['correct'] for r in bad):
                    raise RuntimeError('Excluded outcomes must match the original incomplete-failure policy')
                breakdown.append({'model': spec['model'], 'precision': quant, 'decoder': arm,
                                  'attempts': len(selected), 'token_limit': statuses['token_limit'],
                                  'grammar_trigger_replay_error': statuses['grammar_trigger_replay_error'],
                                  'excluded': len(bad), 'remaining': len(selected)-len(bad),
                                  'failure_categories': dict(Counter(r['category'] for r in bad))})
                failures.extend({k: r[k] for k in ('model', 'quant', 'condition', 'id', 'seed', 'category', 'status', 'raw_source')} for r in bad)
    # Check labels against actual durable raw events, rather than just a derived table.
    failed_keys = {(r['model'], r['quant'], r['condition'], r['id'], r['seed']): r['status'] for r in failures}
    raw_failed, replay_details, token_runtime = {}, [], Counter()
    for source in sorted({r['raw_source'] for r in rows}):
        path = ROOT/source
        source_paths.append(path)
        for line in path.open():
            event = json.loads(line)
            if event['kind'] == 'generation' and event['status'] in EXCLUDED:
                key = (event['model'], event['quant'], event['condition'], event['id'], event['seed'])
                if key in raw_failed:
                    raise RuntimeError('Duplicate raw failure')
                raw_failed[key] = event['status']
                if event['status'] == 'token_limit':
                    response = event['response']
                    token_runtime[response['tokens_predicted'], response['stop_type'],
                                  response['generation_settings']['n_predict']] += 1
                if event['status'] == 'grammar_trigger_replay_error':
                    replay_details.append({k: event[k] for k in ('model', 'quant', 'condition', 'id', 'seed', 'date', 'http_status', 'error_body')})
    if raw_failed != failed_keys:
        raise RuntimeError('Raw and scored failure inventories disagree')
    # Reproduce the original draw sequence exactly when the cohort is unchanged.
    rng = np.random.default_rng(protocol['execution']['bootstrap_seed'])
    reps = protocol['execution']['bootstrap_replicates']
    subsets = {'all': ids, 'required': [i['id'] for i in items if i['category'] != 'irrelevance']}
    subsets.update({category: [i['id'] for i in items if i['category'] == category]
                    for category in sorted({i['category'] for i in items})})
    draws = {name: rng.integers(0, len(sub), (reps, len(sub))) for name, sub in subsets.items()}
    run_draws = rng.integers(0, len(seeds), (reps, len(seeds)))
    cells, effects, contrasts, cohorts = [], [], [], []
    for spec in specs:
        model = spec['model']
        values, eligible = {}, {}
        for quant in precisions:
            for arm in arms:
                panel = [[lookup[model, quant, arm, item, seed] for seed in seeds] for item in ids]
                values[quant, arm] = np.array([[r['score']['correct'] for r in row] for row in panel], dtype=float)
                eligible[quant, arm] = np.array([[r['status'] not in EXCLUDED for r in row] for row in panel])
        panel_mask = np.logical_and.reduce(list(eligible.values()))
        for method in METHODS:
            for subset in ('all', 'required'):
                positions = np.array([ids.index(item) for item in subsets[subset]])
                full_count = len(positions)*len(seeds)
                indices = draws[subset]
                if method == 'complete_item':
                    positions = positions[panel_mask[positions].all(axis=1)]
                    if len(positions) != len(subsets[subset]):
                        # Cohorts differ by model; no cross-model paired contrast is claimed.
                        generator = np.random.default_rng(protocol['execution']['bootstrap_seed'])
                        indices = generator.integers(0, len(positions), (reps, len(positions)))
                estimates, boots, kept = {}, {}, {}
                for key in values:
                    mask = (eligible[key][positions] if method == 'cell_completed'
                            else panel_mask[positions] if method == 'matched_panel'
                            else np.ones((len(positions), len(seeds)), dtype=bool))
                    point, boot = masked_bootstrap(values[key][positions], mask, indices, run_draws)
                    estimates[key], boots[key], kept[key] = point, boot, int(mask.sum())
                    cells.append({'model': model, 'method': method, 'subset': subset, 'precision': key[0],
                                  'decoder': key[1], 'accuracy': point, 'ci95': ci(boot), 'kept_item_run_pairs': int(mask.sum()),
                                  'items_with_observations': int(mask.any(axis=1).sum()),
                                  'kept_by_run': dict(zip(map(str, seeds), map(int, mask.sum(axis=0))))})
                cohorts.append({'model': model, 'method': method, 'subset': subset,
                                'original_item_run_pairs_per_cell': full_count,
                                'kept_per_cell': {q+'/'+a: n for (q, a), n in kept.items()},
                                'retained_item_ids': [ids[p] for p in positions] if method == 'complete_item' else None})
                sensitivity_boots = {}
                for arm in arms[1:]:
                    free = estimates['F16', 'free']-estimates['Q4_K_M', 'free']
                    constrained = estimates['F16', arm]-estimates['Q4_K_M', arm]
                    free_boot = boots['F16', 'free']-boots['Q4_K_M', 'free']
                    constrained_boot = boots['F16', arm]-boots['Q4_K_M', arm]
                    net, net_boot = free-constrained, free_boot-constrained_boot
                    primary = next(r for r in summary['recovery_effects'] if (r['model'], r['subset'], r['decoder']) == (model, subset, arm))
                    bounds = ci(net_boot)
                    effects.append({'model': model, 'method': method, 'subset': subset, 'decoder': arm,
                                    'free_loss': free, 'free_loss_ci95': ci(free_boot),
                                    'constrained_loss': constrained, 'constrained_loss_ci95': ci(constrained_boot),
                                    'net_recovery': net, 'net_recovery_ci95': bounds,
                                    'recovery_share': net/free if free > 0 else None,
                                    'recovery_share_ci95': ci(net_boot/free_boot) if np.all(free_boot > 0) else None,
                                    'ratio_denominator_stable': bool(np.all(free_boot > 0)),
                                    'primary_net_recovery': primary['net_recovery'], 'primary_ci95': primary['net_recovery_ci95'],
                                    'primary_interpretation': interpretation(primary['net_recovery_ci95']),
                                    'sensitivity_interpretation': interpretation(bounds),
                                    'interval_interpretation_changed': interpretation(bounds) != interpretation(primary['net_recovery_ci95']),
                                    'point_sign_changed': bool(interpretation([net, net]) != interpretation([primary['net_recovery']]*2))})
                    sensitivity_boots[arm] = net_boot
                for alternative in ('loose', 'trigger_strict'):
                    boot = sensitivity_boots['whole_strict']-sensitivity_boots[alternative]
                    primary = next(r for r in summary['paired_decoder_contrasts'] if (r['model'], r['subset'], r['contrast']) == (model, subset, 'whole_strict minus '+alternative))
                    point = (estimates['Q4_K_M', 'whole_strict']-estimates['F16', 'whole_strict']
                             -estimates['Q4_K_M', alternative]+estimates['F16', alternative])
                    contrasts.append({'model': model, 'method': method, 'subset': subset,
                                      'contrast': 'whole_strict minus '+alternative,
                                      'incremental_recovery_difference': point, 'ci95': ci(boot),
                                      'primary_difference': primary['incremental_recovery_difference'], 'primary_ci95': primary['ci95'],
                                      'interval_interpretation_changed': interpretation(ci(boot)) != interpretation(primary['ci95'])})
    hashes = {}
    for path in source_paths:
        with path.open('rb') as stream:
            hashes[str(path.relative_to(ROOT))] = hashlib.file_digest(stream, 'sha256').hexdigest()
    result = {'created_at': now(), 'run_id': args.run_id, 'post_hoc': True, 'offline_only': True,
              'excluded_statuses': sorted(EXCLUDED), 'methods': METHODS,
              'bootstrap': {'replicates': reps, 'seed': protocol['execution']['bootstrap_seed'],
                            'unit': 'Crossed original-item/run labels; shared draws across conditions; percentile 95% CIs, unadjusted.',
                            'numerical_zero_tolerance_accuracy_units': ROUND_OFF_TOLERANCE,
                            'complete_item': 'Resample the model-specific retained items at their retained sample size; all five run labels retained.'},
              'warning': 'All exclusions condition on post-treatment completion. Cell-only exclusion changes comparison populations. Matched exclusions remove healthy counterparts too. None replaces the registered failure-inclusive estimand.',
              'original_observations': len(rows), 'excluded_observations': len(failures),
              'failure_counts': dict(Counter(r['status'] for r in failures)), 'failure_breakdown': breakdown,
              'token_limit_runtime': [{'tokens_predicted': k[0], 'stop_type': k[1], 'n_predict': k[2], 'count': count}
                                      for k, count in sorted(token_runtime.items())],
              'failures': failures, 'replay_details': replay_details, 'cohorts': cohorts,
              'scores': cells, 'recovery_effects': effects, 'decoder_contrasts': contrasts,
              'primary_files_sha256': hashes}
    result['exclusion_totals'] = {method: {'retained_observations': sum(r['kept_item_run_pairs'] for r in cells
                                                   if r['method']==method and r['subset']=='all'),
                                         'removed_observations': len(rows)-sum(r['kept_item_run_pairs'] for r in cells
                                                   if r['method']==method and r['subset']=='all')}
                                  for method in METHODS}
    write_json(folder/'failure_sensitivity.json', result)
    with (folder/'failure_breakdown.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(breakdown[0]))
        writer.writeheader();writer.writerows(breakdown)
    lines = ['# Operational failures and exclusion sensitivity', '',
             'Post-hoc analysis of saved outputs only. The registered results still count all operational failures as incorrect.', '',
             '## Failure inventory', '', 'Each cell contains 1,000 attempts. Zero rows are retained.', '',
             '| Model | Precision | Decoder | Token limit | Replay error | Remaining |',
             '| --- | --- | --- | ---: | ---: | ---: |']
    for r in breakdown:
        lines.append(f"| {r['model']} | {r['precision']} | {r['decoder']} | {r['token_limit']} | {r['grammar_trigger_replay_error']} | {r['remaining']} |")
    lines += ['', 'All token-limit runtime combinations (predicted tokens, stop type, configured cap → count): '
              + json.dumps(result['token_limit_runtime'])+'.', '',
              'Replay identifiers and the exact saved server response are in failure_sensitivity.json. No generation was retried.', '']
    lines += ['', '## Exclusion rules and uncertainty', '', result['warning'], '',
              'All intervals use crossed original-item/run resampling with the saved seed and replicate count. Repeated schedules are not independent items. Masked bootstrap means renormalize by retained observations in each draw. No zero-denominator draw is silently discarded. Complete-item analysis resamples only retained items. Different model cohorts prevent a cross-model paired interpretation.', '']
    for method, description in METHODS.items():
        totals=result['exclusion_totals'][method]
        lines += ['### '+method, '', description,
                  f"Across the complete matrix: {totals['retained_observations']} retained observations; {totals['removed_observations']} removed, including healthy matched counterparts where required.", '',
                  '| Model | Subset | F16 free / Q4 free / F16 whole / Q4 whole retained |',
                  '| --- | --- | --- |']
        for cohort in cohorts:
            if cohort['method'] != method:continue
            k = cohort['kept_per_cell']
            lines.append(f"| {cohort['model']} | {cohort['subset']} | {k['F16/free']} / {k['Q4_K_M/free']} / {k['F16/whole_strict']} / {k['Q4_K_M/whole_strict']} |")
        lines += ['', '| Model | Subset | Decoder | Primary recovery [95% CI], pp | Excluded recovery [95% CI], pp | Interval interpretation changed? |',
                  '| --- | --- | --- | --- | --- | --- |']
        for effect in effects:
            if effect['method'] != method:continue
            lines.append(f"| {effect['model']} | {effect['subset']} | {effect['decoder']} | {formatted(effect['primary_net_recovery'],effect['primary_ci95'])} | {formatted(effect['net_recovery'],effect['net_recovery_ci95'])} | {effect['interval_interpretation_changed']} |")
    changed = [r for r in effects if r['interval_interpretation_changed']]
    changed_contrasts = [r for r in contrasts if r['interval_interpretation_changed']]
    headline=[r for r in effects if r['subset']=='required' and r['decoder']=='whole_strict']
    lines += ['', '## Does interpretation change?', '',
              f"Directional interval classifications changed in {len(changed)}/{len(effects)} recovery effects and {len(changed_contrasts)}/{len(contrasts)} decoder contrasts across these rules and both endpoints. Numerical bounds within {ROUND_OFF_TOLERANCE:g} accuracy units of zero count as zero, avoiding a spurious conclusion from floating-point round-off.", '',
              f"Among {len(headline)} method/model combinations for required-call whole-strict recovery, {sum(r['free_loss']<=0 for r in headline)} have nonpositive observed free loss and {sum(r['ratio_denominator_stable'] for r in headline)} have a stable positive bootstrap denominator. The failure-inclusive analysis remains primary.", '']
    lines += ['', '## Reproduce without cloud work', '', '```sh',
              f'.venv/bin/python -m scripts.report_failure_sensitivity --run-id {args.run_id}', '```', '',
              'Full cell accuracies, signed losses, recovery shares, decoder contrasts, run denominators, failed-item IDs and raw replay details are in failure_sensitivity.json. Primary raw/scored files are hashed and left unchanged.', '']
    (folder/'FAILURE_SENSITIVITY.md').write_text('\n'.join(lines))
    print(json.dumps({'failures': result['failure_counts'], 'required_whole_strict': [r for r in effects if r['subset']=='required' and r['decoder']=='whole_strict']}, indent=2))


if __name__ == '__main__':
    main()
