"""Separately approved, bounded A10 Pythonic sensitivity. Primary data untouched."""
import json,subprocess,time
from pathlib import Path
import modal
from full_cloud import app as shared_app,base as shared_base,artifacts,prepare_model
base=shared_base.add_local_file(Path(__file__).resolve().parent/'full_cloud.py','/root/full_cloud.py',copy=True) if modal.is_local() else None
app=modal.App('grammar-vs-bits-pythonic',tags={'project':'grammar-vs-bits','stage':'pythonic'})
app.include(shared_app)

@app.function(image=base,gpu='A10',cpu=(2,2),memory=(16384,16384),volumes={'/artifacts':artifacts},
              timeout=2700,startup_timeout=180,max_containers=1,scaledown_window=2)
def run_pythonic(requests,protocol,metadata):
    from qunti.full_runner import model_worker
    if not protocol.get('sensitivity_only') or len(requests)!=120 or protocol['arms']!=['free','whole_strict']:
        raise RuntimeError('Refuse changed optional matrix')
    yield from model_worker(requests,protocol,metadata,metadata['batch_id'],2500)
    artifacts.commit()

@app.function(image=base,cpu=(.125,.25),memory=(1024,1024),volumes={'/artifacts':artifacts},
              timeout=7200,startup_timeout=180,max_containers=1,scaledown_window=2)
def orchestrate(requests,protocol,spec,app_id,batch_id,resume=None):
    from qunti.common import now
    from qunti.supervision import supervise
    folder=Path('/artifacts/full')/batch_id;folder.mkdir(parents=True,exist_ok=True)
    try:
        start=time.monotonic();metadata=prepare_model.remote(spec)
        metadata.update(batch_id=batch_id,gpu_deadline_seconds=2500,preparation_supervisor_seconds=time.monotonic()-start)
        if resume:
            if not protocol['sensitivity_only'] or not 0<len(resume['keys'])<2400:raise RuntimeError('Invalid optional continuation')
            metadata['completed_generation_keys']=resume['keys']
            metadata['resume_provenance']=resume['provenance']
        with (folder/'events.jsonl').open('a') as stream:stream.write(json.dumps({'kind':'model_prepared','date':now(),'metadata':metadata})+'\n')
        count=0
        for event in supervise(run_pythonic,requests,protocol,metadata,app_id,batch_id,artifacts):
            if event['kind']=='generation':count+=1
            if count%100==0:
                (folder/'progress.json').write_text(json.dumps({'date':now(),'attempts':count,'model':spec['model']})+'\n')
    finally:
        artifacts.commit()
        subprocess.run(['modal','app','stop',app_id,'--yes'],capture_output=True,text=True,timeout=30)
