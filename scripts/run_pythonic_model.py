"""Submit one durable optional job and retrieve its raw checkpoint after shutdown."""
import argparse,json,subprocess
import modal
from qunti.common import ROOT,write_json,now,read_jsonl,digest
from scripts.recover_full_model import wait_for_cloud_stop

def main():
    p=argparse.ArgumentParser();p.add_argument('--batch-id',required=True);p.add_argument('--slug',required=True);p.add_argument('--resume-from');args=p.parse_args()
    from pythonic_cloud import app,orchestrate
    folder=ROOT/'results/sensitivity'/args.batch_id.rsplit('-',1)[0]
    protocol=json.loads((ROOT/'configs/pythonic_protocol.json').read_text())
    spec=next(s for s in json.loads((ROOT/'configs/full_models.json').read_text()) if s['slug']==args.slug)
    requests=json.loads((ROOT/'data/pythonic'/(args.slug+'.json')).read_text())
    resume=None
    if args.resume_from:
        source=ROOT/args.resume_from
        rows=[r for r in read_jsonl(source) if r['kind']=='generation']
        if any(r['model']!=spec['model'] for r in rows):raise RuntimeError('Wrong continuation model')
        keys=[(r['quant'],r['condition'],r['seed'],r['id']) for r in rows]
        if len(set(keys))!=len(keys):raise RuntimeError('Duplicate completed keys')
        resume={'keys':keys,'provenance':{'source':args.resume_from,'sha256':digest(source.read_bytes()),'preserved_observations':len(keys)}}
    app_id=None
    try:
        with modal.enable_output(),app.run(detach=True):
            app_id=app.app_id;app.set_tags({'project':'qunti-check','stage':'pythonic','batch':args.batch_id})
            write_json(folder/(args.batch_id+'_app.json'),{'app_id':app_id,'date':now()})
            call=orchestrate.spawn(requests,protocol,spec,app_id,args.batch_id,resume)
            write_json(folder/(args.batch_id+'_job.json'),{'call_id':call.object_id,'date':now(),'mode':'spawn'})
            try:call.get(timeout=7300)
            except Exception as exc:write_json(folder/(args.batch_id+'_delivery.json'),{'date':now(),'type':type(exc).__name__})
    finally:
        if app_id:
            wait_for_cloud_stop(app_id,7300)
            subprocess.run([str(ROOT/'.venv/bin/modal'),'app','stop',app_id,'--yes'],capture_output=True,text=True,timeout=60)
            for name,cmd in [('apps',['app','list','--json','--limit','0']),('containers',['container','list','--json'])]:
                r=subprocess.run([str(ROOT/'.venv/bin/modal'),*cmd],capture_output=True,text=True,timeout=60,check=True)
                write_json(folder/(args.batch_id+'_shutdown_'+name+'.json'),json.loads(r.stdout))
    volume=modal.Volume.from_name('qunti-check-artifacts',create_if_missing=False)
    target=folder/(args.batch_id+'.jsonl');temporary=target.with_suffix('.download')
    with temporary.open('wb') as stream:volume.read_file_into_fileobj('/full/'+args.batch_id+'/events.jsonl',stream)
    temporary.replace(target)
    print('Retrieved durable checkpoint without repeating inference.')

if __name__=='__main__':main()
