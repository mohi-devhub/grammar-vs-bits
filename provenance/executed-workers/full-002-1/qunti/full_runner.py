"""A10-only, fixed-matrix model worker. No benchmark labels enter generation."""
import json
import platform
import random
import subprocess
import sys
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from qunti.common import digest, now
from qunti.runner import request, LLAMA_COMMIT
from qunti.grammar import literal


def decoding(item, arm, family):
    if arm == 'free':
        return {}
    out = {'grammar': item['grammars'][arm], 'grammar_lazy': arm == 'trigger_strict'}
    if arm == 'trigger_strict':
        if family == 'qwen':
            out['preserved_tokens'] = ['<tool_call>']
            out['grammar_triggers'] = [{'type': 1, 'value': '<tool_call>'}]
        else:
            # A word trigger can become one exact token and miss merged '{"'.
            # One pattern finds the earliest object OR array opener in a piece.
            out['grammar_triggers'] = [{'type': 2, 'value': r'(\[|\{)'}]
    return out


def trigger_probes(family):
    targets = [('<tool_call>', '<tool_call>{"name":"allowed","arguments":{}}</tool_call>')] if family == 'qwen' else [
        ('{', '{"name":"allowed","parameters":{}}'), ('[', '[{"name":"allowed","parameters":{}}]')]
    results = []
    for prefix, target in targets:
        ids = request('/tokenize', {'content': target, 'add_special': False, 'parse_special': True})['tokens']
        if not ids:
            raise RuntimeError('Synthetic trigger preflight needs a target token')
        trigger = {'type': 1, 'value': prefix} if family == 'qwen' else {'type': 2, 'value': r'(\[|\{)'}
        payload = {'prompt': 'Output a tool call now.', 'temperature': 0, 'seed': 101,
                   'n_predict': 128, 'cache_prompt': False,
                   'grammar': 'root ::= ' + literal(target) + '\n',
                   'grammar_lazy': True, 'grammar_triggers': [trigger],
                   'preserved_tokens': [prefix] if family == 'qwen' else [],
                   'logit_bias': [[ids[0], 1000]]}
        result = request('/completion', payload)
        settings = result.get('generation_settings', {})
        passed = (result.get('content', '').strip() == target and settings.get('grammar_lazy') is True
                  and bool(settings.get('grammar_triggers')) and result.get('stop_type') != 'limit')
        results.append({'prefix': prefix, 'target': target, 'payload': payload, 'response': result, 'passed': passed})
    return results


def model_worker(requests, protocol, metadata, batch_id, max_seconds):
    start = time.monotonic()
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader'], text=True).strip()
    if 'A10' not in gpu.split(',')[0]:
        raise RuntimeError('Full run requires A10; no hardware fallback is authorized')
    meta = {'date': now(), 'gpu': gpu, 'gpu_type': 'A10', 'gpu_name': gpu.split(',')[0],
            'python': sys.version, 'platform': platform.platform(), 'llama_cpp_commit': LLAMA_COMMIT,
            'protocol_sha256': digest(protocol), 'batch_id': batch_id, 'model': metadata['model']}
    yield {'kind': 'session_started', 'metadata': meta}
    folder = Path('/artifacts/full') / batch_id
    folder.mkdir(parents=True, exist_ok=True)
    count = 0
    for precision in protocol['precisions']:
        if time.monotonic() - start >= max_seconds - 120:
            yield {'kind': 'budget_stop', 'date': now(), 'completed_generations': count}
            return
        path = Path(metadata['model_dir']) / (precision + '.gguf')
        if path.stat().st_size != metadata['artifacts'][precision]['bytes']:
            raise RuntimeError('GGUF size does not match prepared manifest')
        cmd = ['/opt/llama-build/bin/llama-server', '-m', str(path), '--host', '127.0.0.1', '--port', '8080',
               '-ngl', '99', '-t', '2', '-tb', '2', '-np', str(protocol['parallel_slots']),
               '-c', str(protocol['parallel_slots'] * protocol['context_per_slot']), '-ctk', 'f16', '-ctv', 'f16', '-fa', 'on', '--no-warmup']
        log_path = folder / (precision + '-server.log')
        with log_path.open('w') as log:
            server = subprocess.Popen(cmd, stdout=log, stderr=log)
            load_started = time.monotonic()
            try:
                while True:
                    if server.poll() is not None:
                        raise RuntimeError('llama-server exited during model loading')
                    try:
                        request('/health', timeout=2)
                        break
                    except (urllib.error.URLError, TimeoutError):
                        if time.monotonic() - load_started > 120:
                            raise TimeoutError('Server load deadline')
                        time.sleep(.2)
                props = request('/props')
                warm = request('/completion', {'prompt': 'Hello', 'n_predict': 1, 'temperature': 0, 'cache_prompt': False, 'seed': 101})
                yield {'kind': 'model_loaded', 'precision': precision, 'date': now(), 'load_seconds': time.monotonic()-load_started,
                       'command': cmd, 'props': props, 'warmup': warm, 'model_metadata': metadata['artifacts'][precision]}
                if precision == protocol['precisions'][0]:
                    probes = trigger_probes(metadata['family'])
                    yield {'kind': 'trigger_preflight', 'probes': probes, 'passed': all(p['passed'] for p in probes)}
                    if not all(p['passed'] for p in probes):
                        raise RuntimeError('Lazy-trigger runtime preflight failed; do not run a mislabeled arm')
                for seed in protocol['run_seeds']:
                    if time.monotonic() - start >= max_seconds - 90:
                        yield {'kind': 'budget_stop', 'date': now(), 'completed_generations': count}
                        return
                    jobs = [(i, arm) for i in requests for arm in protocol['arms']]
                    random.Random(f"full:{metadata['model']}:{precision}:{seed}").shuffle(jobs)
                    batch_started = time.monotonic()
                    def generate(job):
                        item, arm = job
                        t = time.monotonic()
                        row = {'kind': 'generation', 'batch_id': batch_id, 'id': item['id'], 'category': item['category'],
                               'model': metadata['model'], 'model_revision': metadata['revision'], 'family': metadata['family'],
                               'quant': precision, 'condition': arm, 'seed': seed, 'run': str(seed), 'date': now(),
                               'gpu_type': 'A10', 'gpu_name': meta['gpu_name'], 'llama_cpp_commit': LLAMA_COMMIT,
                               'input_sha256': item['input_sha256'], 'schema_sha256': item['schema_sha256'],
                               'prompt_sha256': digest(item['prompt'].encode()),
                               'grammar_sha256': digest(item['grammars'][arm].encode()) if arm != 'free' else None}
                        if time.monotonic() - start >= max_seconds - 60:
                            row.update(status='not_run_budget', text='', completed=False, elapsed_seconds=0.0)
                            return row
                        payload = {'prompt': item['prompt'], 'temperature': 0.0, 'seed': seed, 'n_predict': protocol['max_output_tokens'],
                                   'cache_prompt': False, 'return_tokens': True, 'stream': False, **decoding(item, arm, metadata['family'])}
                        try:
                            row['input_tokens'] = len(request('/tokenize', {'content': item['prompt'], 'add_special': True})['tokens'])
                            if row['input_tokens'] + protocol['max_output_tokens'] > protocol['context_per_slot']:
                                row.update(status='context_overflow', text='', completed=False)
                            else:
                                response = request('/completion', payload)
                                limited = response.get('stopped_limit', response.get('stop_type') == 'limit')
                                row.update(status='token_limit' if limited else 'ok', text=response.get('content',''), completed=not limited, response=response)
                                settings = response.get('generation_settings', {})
                                if arm == 'trigger_strict' and (settings.get('grammar_lazy') is not True or not settings.get('grammar_triggers')):
                                    row.update(status='constraint_configuration_error', completed=False)
                        except Exception as exc:
                            row.update(status='request_error', text='', completed=False, error_type=type(exc).__name__)
                            if isinstance(exc, urllib.error.HTTPError):
                                row['http_status'] = exc.code
                                row['error_body'] = exc.read().decode(errors='replace')[:3000]
                        row['elapsed_seconds'] = time.monotonic() - t
                        return row
                    statuses = []
                    with ThreadPoolExecutor(max_workers=protocol['parallel_slots']) as pool:
                        for future in as_completed([pool.submit(generate, job) for job in jobs]):
                            row = future.result();count += 1;statuses.append(row['status'])
                            with (folder / 'raw.jsonl').open('a') as raw:
                                raw.write(json.dumps(row,ensure_ascii=False)+'\n')
                            yield row
                    yield {'kind': 'run_finished', 'precision': precision, 'seed': seed, 'batch_wall_seconds': time.monotonic()-batch_started,
                           'attempted_generations':len(jobs), 'date':now()}
                    if 'not_run_budget' in statuses:
                        yield {'kind':'budget_stop','date':now(),'completed_generations':count}
                        return
                    if any(s in ('request_error','constraint_configuration_error') for s in statuses):
                        raise RuntimeError('Operational error in completed run; preserve failures and stop before further runs')
            except Exception as exc:
                log.flush()
                yield {'kind':'worker_error','error_type':type(exc).__name__,'precision':precision,'server_log_tail':log_path.read_text()[-20000:]}
                raise
            finally:
                server.terminate()
                try: server.wait(timeout=15)
                except subprocess.TimeoutExpired: server.kill();server.wait()
        yield {'kind':'server_log','precision':precision,'text':log_path.read_text()[-20000:]}
    yield {'kind':'session_finished','attempted_generations':count,'active_function_seconds':time.monotonic()-start,
           'metadata':meta,'pip_audit':json.loads(Path('/opt/pip-audit.json').read_text())}
