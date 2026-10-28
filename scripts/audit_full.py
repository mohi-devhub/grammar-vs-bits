"""Verify the real saved matrix, completion statuses and metadata before reporting."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import statistics
from qunti.common import ROOT, now, read_jsonl, write_json,digest
from qunti.runner import LLAMA_COMMIT


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    args = p.parse_args()
    protocol = json.loads((ROOT / 'configs/protocol.json').read_text())
    specs = json.loads((ROOT / 'configs/full_models.json').read_text())
    state=json.loads((ROOT/'results/full'/args.run_id/'state.json').read_text())
    batches={r['model']:r['batch_id'] for r in state['model_sessions']}
    ids = {r['id'] for r in read_jsonl(ROOT / 'data/frozen.jsonl')}
    models = []
    for index, spec in enumerate(specs):
        source = ROOT / 'results/full' / batches.get(spec['model'],f'{args.run_id}-{index + 1}') / 'events.jsonl'
        if not source.exists():
            models.append({'model': spec['model'], 'complete': False, 'reason': 'not started'})
            continue
        events = read_jsonl(source)
        rows = [r for r in events if r['kind'] == 'generation']
        expected = {(q, a, s, i) for q in protocol['precisions'] for a in protocol['arms'] for s in protocol['run_seeds'] for i in ids}
        keys = [(r['quant'], r['condition'], r['seed'], r['id']) for r in rows]
        problems = []
        if len(set(keys)) != len(keys): problems.append('duplicate observations')
        if set(keys) - expected: problems.append('unexpected observations')
        if any(r['gpu_type'] != 'A10' or 'A10' not in r['gpu_name'] for r in rows): problems.append('GPU policy violation')
        if any(r['model'] != spec['model'] or r['model_revision'] != spec['revision'] for r in rows): problems.append('model provenance mismatch')
        if any(r['llama_cpp_commit']!=LLAMA_COMMIT for r in rows):problems.append('inference source pin mismatch')
        if any(r['response']['generation_settings'].get('temperature')!=protocol['temperature']
               or r['response']['generation_settings'].get('n_predict')!=protocol['max_output_tokens']
               or r['response']['generation_settings'].get('seed')!=r['seed'] for r in rows if 'response' in r):
            problems.append('observed sampling settings mismatch')
        for loaded in [e for e in events if e['kind']=='model_loaded']:
            command=loaded['command']
            expected_args={'-np':str(protocol['parallel_slots']),'-c':str(protocol['parallel_slots']*protocol['context_per_slot']),
                           '-ctk':protocol['cache_type_k'],'-ctv':protocol['cache_type_v']}
            if any(flag not in command or command[command.index(flag)+1]!=value for flag,value in expected_args.items()):
                problems.append('recorded server configuration mismatch')
            if loaded['props']['total_slots']!=protocol['parallel_slots']:problems.append('observed server slot count mismatch')
            if loaded['props']['model_ftype']!={'F16':'F16','Q4_K_M':'Q4_K - Medium'}[loaded['precision']]:
                problems.append('observed GGUF precision label mismatch')
        requests=json.loads((ROOT/'data/full_requests'/(spec['slug']+'.json')).read_text())
        expected_hashes={r['id']:{'input_sha256':r['input_sha256'],'schema_sha256':r['schema_sha256'],
                          'prompt_sha256':digest(r['prompt'].encode()),
                          'grammars':{a:digest(g.encode()) for a,g in r['grammars'].items()}} for r in requests}
        for row in rows:
            wanted=expected_hashes[row['id']]
            if any(row[k]!=wanted[k] for k in ('input_sha256','schema_sha256','prompt_sha256')):
                problems.append('frozen input hash mismatch');break
            if row['grammar_sha256']!=(None if row['condition']=='free' else wanted['grammars'][row['condition']]):
                problems.append('frozen grammar hash mismatch');break
        if spec['family']=='llama' and any(r.get('prompt_transport')!='native_token_ids' or r.get('first_prompt_token_ids',[None])[0]!=128000
             or r.get('first_prompt_token_ids',[])[1:2]==[128000] for r in rows):
            problems.append('native Llama single-BOS transport mismatch')
        cells = defaultdict(list)
        for row in rows:
            cells[row['quant'], row['condition']].append(row)
        summaries = []
        for (q, arm), values in sorted(cells.items()):
            durations = [r['elapsed_seconds'] for r in values]
            predicted = [r['response']['tokens_predicted'] for r in values if 'response' in r]
            summaries.append({'precision': q, 'decoder': arm, 'attempts': len(values),
                              'status_counts': dict(Counter(r['status'] for r in values)),
                              'completed': sum(r['completed'] for r in values),
                              'elapsed_seconds_median': statistics.median(durations),
                              'elapsed_seconds_range': [min(durations), max(durations)],
                              'predicted_tokens_total': sum(predicted),
                              'predicted_tokens_median': statistics.median(predicted) if predicted else None})
        complete = set(keys) == expected and not problems and any(e['kind'] == 'session_finished' for e in events)
        models.append({'model': spec['model'], 'complete': complete, 'attempts': len(rows),
                       'missing_observations': len(expected - set(keys)), 'problems': problems, 'cells': summaries,
                       'source': str(source.relative_to(ROOT)), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                       'gpu_names': sorted({r['gpu_name'] for r in rows}),
                       'llama_cpp_commits': sorted({r['llama_cpp_commit'] for r in rows}),
                       'runtime_probe_events': [e for e in events if e['kind'] == 'trigger_preflight']})
    result = {'created_at': now(), 'run_id': args.run_id, 'complete': all(m['complete'] for m in models),
              'controlled_inference_settings':{k:protocol[k] for k in ('temperature','parallel_slots','context_per_slot','max_output_tokens','cache_type_k','cache_type_v')},
              'models': models, 'latency_scope': 'Per-request wall time including tokenization, serving and slot contention; not isolated GPU kernel time. Tokens and operational failures retained.'}
    write_json(ROOT / 'results/full' / args.run_id / 'integrity.json', result)
    print(json.dumps({'complete': result['complete'], 'models': [{k: v for k, v in m.items() if k in ('model', 'complete', 'attempts', 'missing_observations', 'problems')} for m in models]}, indent=2))
    if any(m.get('problems') for m in models):
        raise RuntimeError('Saved matrix failed its integrity checks')


if __name__ == '__main__':
    main()
