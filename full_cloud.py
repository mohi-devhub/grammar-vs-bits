"""Approved A10-only full model sessions using the exact audited pilot runtime."""
import json
import os
from pathlib import Path
import modal

ROOT=Path(__file__).resolve().parent
app=modal.App('qunti-check-full',tags={'project':'qunti-check','stage':'full'})
artifacts=modal.Volume.from_name('qunti-check-artifacts',create_if_missing=True)
base=None
if modal.is_local():
    if os.environ.get('QUNTI_REBUILD_FROM_SOURCE')=='1':
        from cloud import base
    else:
        base=modal.Image.from_id('im-bn1uCAy12LO075Ds0NhzwA').add_local_dir(
            os.environ.get('QUNTI_WORKER_SOURCE',str(ROOT/'qunti')),'/root/qunti',copy=True)


@app.function(image=base,cpu=(2,2),memory=(16384,16384),volumes={'/artifacts':artifacts},
              secrets=[modal.Secret.from_name('huggingface')],timeout=1800,max_containers=1,retries=0,scaledown_window=2)
def prepare_model(spec):
    import hashlib
    import shutil
    import subprocess
    import time
    import sys
    from huggingface_hub import snapshot_download
    from qunti.common import now
    start=time.monotonic()
    audit_path=Path('/artifacts/full')/(spec['slug']+'-pip-audit.json')
    audit_path.parent.mkdir(parents=True,exist_ok=True)
    audit=subprocess.run(['python','-m','pip_audit','--local','--format','json','--output',str(audit_path)],capture_output=True,text=True,timeout=180)
    if audit.returncode:
        artifacts.commit()
        raise RuntimeError('Fresh Linux dependency audit failed; do not launch a GPU')
    target=Path('/artifacts/models')/spec['slug'];target.mkdir(parents=True,exist_ok=True)
    manifest=target/'manifest.json'
    def sha(p):
        with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
    if manifest.exists():
        old=json.loads(manifest.read_text())
        if old['model']==spec['model'] and old['revision']==spec['revision'] and all(
            (target/(q+'.gguf')).exists() and sha(target/(q+'.gguf'))==old['artifacts'][q]['sha256'] for q in ('F16','Q4_K_M')):
            return {**old,'artifacts':{q:old['artifacts'][q] for q in ('F16','Q4_K_M')},'model_dir':str(target),
                    'family':spec['family'],'artifact_reused':True,'active_function_seconds':time.monotonic()-start}
    hf=target/'hf'
    snapshot_download(spec['model'],revision=spec['revision'],local_dir=str(hf),
                      allow_patterns=['*.safetensors','*.json','*.jinja','tokenizer.model','*.txt','LICENSE*','README.md'],max_workers=4)
    hashes={str(p.relative_to(hf)):sha(p) for p in hf.rglob('*') if p.is_file() and '.cache' not in p.parts}
    commands=[['python','/opt/llama.cpp/convert_hf_to_gguf.py',str(hf),'--outfile',str(target/'F16.gguf'),'--outtype','f16'],
              ['/opt/llama-cpu/bin/llama-quantize',str(target/'F16.gguf'),str(target/'Q4_K_M.gguf'),'Q4_K_M','2']]
    for cmd in commands:
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=900)
        if result.returncode:
            (target/'preparation_failure.log').write_text(result.stdout+result.stderr);artifacts.commit()
            raise RuntimeError('Local-file conversion/quantization failed; diagnostic retained on volume')
    out={**spec,'model_dir':str(target),'date':now(),'source_file_sha256':hashes,'commands':commands,'python':sys.version,
         'llama_cpp_commit':'8542e94350f0ade01644db6f1d1520da3814dafd',
         'artifacts':{q:{'sha256':sha(target/(q+'.gguf')),'bytes':(target/(q+'.gguf')).stat().st_size} for q in ('F16','Q4_K_M')},
         'active_function_seconds':time.monotonic()-start}
    manifest.write_text(json.dumps(out,indent=2)+'\n')
    for p in hf.glob('*.safetensors'):p.unlink()
    shutil.rmtree(hf/'.cache',ignore_errors=True)
    artifacts.commit()
    return out


@app.function(image=base,gpu='A10',cpu=(2,2),memory=(16384,16384),volumes={'/artifacts':artifacts},
              timeout=14400,startup_timeout=180,max_containers=1,scaledown_window=2)
def run_model(requests,protocol,metadata):
    from qunti.full_runner import model_worker
    if not protocol.get('full_run_approved') or len(requests)!=200 or protocol['full_run_generations']!=24000:
        raise RuntimeError('Refusing unapproved or changed full matrix')
    yield from model_worker(requests,protocol,metadata,metadata['batch_id'],metadata['gpu_deadline_seconds'])
    artifacts.commit()


@app.function(image=base,cpu=(0.125,0.25),memory=(1024,1024),volumes={'/artifacts':artifacts},
              timeout=16500,startup_timeout=180,max_containers=1,scaledown_window=2)
def supervise_model(requests,protocol,metadata,app_id,batch_id):
    from qunti.supervision import supervise
    yield from supervise(run_model,requests,protocol,metadata,app_id,batch_id,artifacts)


@app.function(image=base,cpu=(0.125,0.25),memory=(1024,1024),volumes={'/artifacts':artifacts},
              timeout=16500,startup_timeout=180,max_containers=1,scaledown_window=2)
def orchestrate_model(requests,protocol,spec,app_id,batch_id,gpu_seconds):
    """Submit preparation and inference in the cloud, independent of the laptop."""
    import subprocess
    import time
    from qunti.common import now
    from qunti.supervision import supervise
    folder=Path('/artifacts/full')/batch_id;folder.mkdir(parents=True,exist_ok=True)
    def record(event):
        with (folder/'events.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
        return event
    record({'kind':'orchestrator_started','date':now(),'batch_id':batch_id})
    start=time.monotonic()
    try:
        metadata=prepare_model.remote(spec)
        metadata.update(batch_id=batch_id,gpu_deadline_seconds=gpu_seconds,
                        preparation_supervisor_seconds=time.monotonic()-start)
        (folder/'model_artifacts.json').write_text(json.dumps(metadata)+'\n')
        record({'kind':'model_prepared','date':now(),'metadata':metadata})
        count=0
        for event in supervise(run_model,requests,protocol,metadata,app_id,batch_id,artifacts):
            if event['kind']=='generation':count+=1
            if event['kind']!='generation' or count%200==0:
                (folder/'progress.json').write_text(json.dumps({'date':now(),'batch_id':batch_id,'kind':event['kind'],
                    'attempts':count,'model':spec['model']})+'\n')
                print(spec['slug']+': '+str(count)+'/8000; '+event['kind'],flush=True)
    finally:
        artifacts.commit()
        subprocess.run(['modal','app','stop',app_id,'--yes'],capture_output=True,text=True,timeout=30)


@app.function(image=base,cpu=(0.125,0.25),memory=(1024,1024),volumes={'/artifacts':artifacts},
              timeout=120,max_containers=1,scaledown_window=2)
def detachment_probe(app_id,probe_id):
    import subprocess
    import time
    from qunti.common import now
    started=now();clock=time.monotonic()
    time.sleep(35)
    path=Path('/artifacts/ops')/(probe_id+'.json');path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({'probe':probe_id,'started_at':started,'completed_at':now(),
        'active_function_seconds':time.monotonic()-clock,'gpu_used':False,'complete':True})+'\n')
    artifacts.commit()
    subprocess.run(['modal','app','stop',app_id,'--yes'],capture_output=True,text=True,timeout=30)
