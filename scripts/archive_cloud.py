"""Archive project outputs and provenance before any remote cache cleanup."""
import argparse
import hashlib
import json
from pathlib import PurePosixPath
import shutil
import modal
from modal.types import FileEntryType
from qunti.common import ROOT,now,write_json
from scripts.pilot import app_snapshot


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--plan-only',action='store_true');args=p.parse_args()
    state=json.loads((ROOT/'results/full'/args.run_id/'state.json').read_text())
    if not args.plan_only and not state.get('complete'):
        raise RuntimeError('Complete collection before archiving its final provenance')
    if not args.plan_only and any(a['state']!='stopped' and a.get('description','').startswith('qunti-check') for a in app_snapshot()):
        raise RuntimeError('Stop this project before archiving mutable cloud outputs')
    volume=modal.Volume.from_name('qunti-check-artifacts',create_if_missing=False)
    entries=[];excluded_bytes=0
    for entry in volume.iterdir('/',recursive=True):
        if entry.type!=FileEntryType.FILE:continue
        path=PurePosixPath(entry.path.lstrip('/'))
        if '..' in path.parts:raise RuntimeError('Unsafe remote path')
        if path.parts[0]=='models' and path.name not in ('manifest.json','preparation_failure.log'):
            excluded_bytes+=entry.size;continue
        entries.append((entry,path))
    size=sum(e.size for e,path in entries)
    plan={'date':now(),'volume':'qunti-check-artifacts','files':len(entries),'bytes_to_archive':size,
          'excluded_reproducible_model_cache_bytes':excluded_bytes,'deletion_performed':False}
    write_json(ROOT/'results/ops'/f'{args.run_id}_cloud_archive_plan.json',plan)
    if args.plan_only:
        print(json.dumps(plan,indent=2));return
    if shutil.disk_usage(ROOT).free<size+512*1024**2:
        raise RuntimeError('Insufficient disk for the cloud archive plus working margin')
    destination=ROOT/'results/cloud_archive';destination.mkdir(parents=True,exist_ok=True)
    inventory=[]
    for entry,path in entries:
        local=destination.joinpath(*path.parts);local.parent.mkdir(parents=True,exist_ok=True)
        temporary=local.with_name(local.name+'.download')
        with temporary.open('wb') as f:volume.read_file_into_fileobj(entry.path,f)
        if temporary.stat().st_size!=entry.size:raise RuntimeError('Remote/local archive size mismatch')
        with temporary.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
        temporary.replace(local)
        inventory.append({'remote_path':entry.path,'local_path':str(local.relative_to(ROOT)),'bytes':entry.size,'sha256':sha})
    write_json(ROOT/'results/ops'/f'{args.run_id}_cloud_archive.json',{**plan,'completed_at':now(),'complete':True,'inventory':inventory})
    print('Archived '+str(len(inventory))+' files with byte counts and SHA-256 hashes. No remote deletion performed.')


if __name__=='__main__':main()
