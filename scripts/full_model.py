"""One separately budgeted model session, with fixed A10 and durable cloud supervision."""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from qunti.common import ROOT, now, write_json
from scripts.pilot import wait_for_evalnoise, freeze_worker_source


def main():
    p=argparse.ArgumentParser();p.add_argument('--slug',required=True);p.add_argument('--batch-id',required=True)
    p.add_argument('--gpu-seconds',type=int,required=True);args=p.parse_args()
    protocol=json.loads((ROOT/'configs/protocol.json').read_text())
    spec=next(x for x in json.loads((ROOT/'configs/full_models.json').read_text()) if x['slug']==args.slug)
    requests=json.loads((ROOT/'data/full_requests'/(args.slug+'.json')).read_text())
    allow_studies=protocol['execution'].get('allow_concurrent_evalnoise_studies',False)
    wait_for_evalnoise(args.batch_id,allow_studies);freeze_worker_source(args.batch_id)
    import modal
    from full_cloud import app, orchestrate_model
    started=time.monotonic();app_id=None;count=0;gpu_finished=False
    folder=ROOT/'results/full'/args.batch_id;folder.mkdir(parents=True,exist_ok=True)
    try:
        with modal.enable_output():
            with app.run(detach=True):
                app_id=app.app_id
                app.set_tags({'project':'qunti-check','stage':'full','batch':args.batch_id,'model':args.slug})
                write_json(ROOT/f'results/ops/{args.batch_id}_app.json',{'app_id':app_id,'date':now(),'model':spec['model']})
                wait_for_evalnoise(args.batch_id,allow_studies)
                with (folder/'events.jsonl').open('w') as f:
                    try:
                        call=orchestrate_model.spawn(requests,protocol,spec,app_id,args.batch_id,args.gpu_seconds)
                        write_json(folder/'submitted_job.json',{'date':now(),'app_id':app_id,'function_call_id':call.object_id,
                            'submission':'spawn; cloud worker lifetime independent of local result stream'})
                        print('Submitted detached cloud job '+call.object_id,flush=True)
                        call.get(timeout=args.gpu_seconds+3900)
                    except Exception as exc:
                        write_json(folder/'stream_ending.json',{'date':now(),'exception_type':type(exc).__name__,'received':count,'gpu_finished':gpu_finished})
                        # The cloud app can finish before the large client stream
                        # drains. Verify its durable checkpoint after shutdown.
    finally:
        app_id=app_id or app.app_id
        # A client disconnect is not evidence that detached cloud work failed.
        # Its watchdog owns the queue/runtime limits and normal self-shutdown.
        if app_id and not gpu_finished:
            from scripts.recover_full_model import wait_for_cloud_stop
            wait_for_cloud_stop(app_id,args.gpu_seconds+3900)
        if app_id:subprocess.run([str(ROOT/'.venv/bin/modal'),'app','stop',app_id,'--yes'],capture_output=True,text=True,timeout=60)
        write_json(folder/'client_timing.json',{'date':now(),'seconds':time.monotonic()-started,'received':count,'gpu_finished':gpu_finished,'app_id':app_id})
        for name,cmd in [('apps',['app','list','--json','--limit','0']),('containers',['container','list','--json'])]:
            r=subprocess.run([str(ROOT/'.venv/bin/modal'),*cmd],capture_output=True,text=True,timeout=60)
            if r.returncode==0:write_json(folder/('shutdown_'+name+'.json'),json.loads(r.stdout))
    if count!=8000 or not gpu_finished:
        from scripts.recover_full_model import download_and_adopt
        download_and_adopt(args.batch_id)
        write_json(folder/'client_recovery.json',{'date':now(),'local_received':count,'cloud_verified':8000,
                    'original_stream_had_completion':gpu_finished,'inference_repeated':False})


if __name__=='__main__':main()
