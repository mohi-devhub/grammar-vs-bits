"""Cloud-side queue/interlock watchdog and durable event relay; no model inference."""
import json
import re
import subprocess
import threading
import time
from pathlib import Path
from qunti.common import now


def cli(*args):
    result = subprocess.run(['modal', *args], capture_output=True, text=True, timeout=30)
    if result.returncode:
        detail=re.sub(r'\b(?:hf_[A-Za-z0-9]+|ak-[A-Za-z0-9_-]+|as-[A-Za-z0-9_-]+)\b','[REDACTED]',result.stderr[-1200:])
        detail=re.sub(r'(https?://[^\s?]+)\?[^\s]+',r'\1?[REDACTED]',detail)
        raise RuntimeError('Cloud control command status '+str(result.returncode)+': '+detail)
    return json.loads(result.stdout) if result.stdout.strip().startswith(('[', '{')) else None


def supervise(worker, requests, protocol, metadata, app_id, batch_id, volume):
    # Validate control-plane access BEFORE requesting a GPU.
    cli('app', 'list', '--json', '--limit', '0')
    folder = Path('/artifacts') / ('full' if protocol.get('stage') == 'full' else 'pilot') / batch_id
    folder.mkdir(parents=True, exist_ok=True)
    events = folder / 'events.jsonl'
    started = time.monotonic()
    gpu_started = threading.Event()
    done = threading.Event()
    limit = protocol.get('execution', protocol['pilot'])['queue_wait_seconds']
    gpu_clock = {}
    def persist(event):
        with events.open('a') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        return event
    def stop_app(reason):
        record={'date':now(),'reason':reason,'app_id':app_id}
        with (folder/'shutdown_history.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
        first=folder/'shutdown_reason.json'
        if not first.exists():first.write_text(json.dumps(record)+'\n')
        try:
            volume.commit()
        finally:
            subprocess.run(['modal', 'app', 'stop', app_id, '--yes'], capture_output=True, text=True, timeout=30)
    def watch():
        failures=0
        while not done.wait(5):
            reason = None
            try:
                busy = [a for a in cli('app', 'list', '--json', '--limit', '0')
                        if a.get('state') != 'stopped' and any(x in a.get('description', '').lower() for x in ('evalnoise', 'noise-check'))]
                if busy:
                    reason = 'evalnoise became active; stop only our app'
                failures=0
                if gpu_started.is_set() and metadata.get('gpu_deadline_seconds') and time.monotonic() - gpu_clock['start'] > metadata['gpu_deadline_seconds'] + 60:
                    reason = 'GPU model budget deadline reached'
                if not gpu_started.is_set() and time.monotonic() - started >= limit:
                    reason = 'Neither approved GPU started within the 1800-second cloud-side wait'
            except Exception as exc:
                failures+=1
                with (folder/'control_errors.jsonl').open('a') as f:
                    f.write(json.dumps({'date':now(),'consecutive_failures':failures,'error_type':type(exc).__name__,'detail':str(exc)})+'\n')
                if failures>=3:
                    reason = 'Unable to verify evalnoise interlock after three status checks; fail closed'
            if reason:
                stop_app(reason)
                return
    monitor = threading.Thread(target=watch, daemon=True)
    monitor.start()
    yield persist({'kind': 'supervisor_ready', 'date': now(), 'queue_wait_seconds': limit, 'durable_event_path': str(events)})
    try:
        for event in worker.remote_gen(requests, protocol, metadata):
            if event['kind'] == 'session_started':
                if gpu_started.is_set():
                    raise RuntimeError('Multiple GPU sessions within one pilot are forbidden')
                gpu_clock['start'] = time.monotonic()
                gpu_started.set()
            yield persist(event)
        yield persist({'kind': 'supervisor_finished', 'date': now(), 'active_function_seconds': time.monotonic() - started})
    except Exception as exc:
        persist({'kind': 'supervisor_error', 'date': now(), 'error_type': type(exc).__name__})
        raise
    finally:
        done.set()
        # Result checkpoint survives laptop/network loss. App self-stop is intentional;
        # local completion is established by the saved GPU session_finished + coverage.
        try:
            volume.commit()
        finally:
            time.sleep(5)
            stop_app('Supervisor ending; stop our app after durable checkpoint')
