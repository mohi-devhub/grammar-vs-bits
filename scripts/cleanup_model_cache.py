"""Remove regenerable GGUF files after verifying the local provenance archive."""
import argparse
import hashlib
import json
from pathlib import PurePosixPath

import modal
from modal.types import FileEntryType

from qunti.common import ROOT, now, write_json
from scripts.pilot import app_snapshot


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--record-id',help='Separate cleanup record; preserve earlier cleanup history')
    args=parser.parse_args()
    folder=ROOT/'results/full'/args.run_id
    if not json.loads((folder/'state.json').read_text())['complete']:
        raise RuntimeError('Finish collection before removing model caches')
    archive=json.loads((ROOT/'results/ops'/f'{args.run_id}_cloud_archive.json').read_text())
    if not archive['complete'] or archive['volume']!='qunti-check-artifacts':
        raise RuntimeError('A complete archive of this project is required')
    for record in archive['inventory']:
        path=ROOT/record['local_path']
        with path.open('rb') as stream:
            sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if path.stat().st_size!=record['bytes'] or sha!=record['sha256']:
            raise RuntimeError('Local provenance archive failed verification')
    if any(a['state']!='stopped' and a.get('description','').startswith('qunti-check') for a in app_snapshot()):
        raise RuntimeError('Stop this project before removing its model caches')
    volume=modal.Volume.from_name('qunti-check-artifacts',create_if_missing=False)
    targets=[]
    for entry in volume.iterdir('/models',recursive=True):
        path=PurePosixPath(entry.path.lstrip('/'))
        if '..' in path.parts or path.parts[0]!='models':
            raise RuntimeError('Unexpected model-cache path')
        if entry.type==FileEntryType.FILE and path.suffix=='.gguf':
            targets.append({'path':entry.path,'bytes':entry.size})
    record={'date':now(),'volume':'qunti-check-artifacts','complete':False,
            'scope':'Regenerable GGUF weight files only; manifests and all raw cloud outputs retained.',
            'verified_archive':f"results/ops/{args.run_id}_cloud_archive.json",'targets':targets}
    output=ROOT/'results/ops'/f'{args.record_id or args.run_id}_model_cache_cleanup.json'
    write_json(output,record)
    for target in targets:
        volume.remove_file(target['path'])
    remaining=[e.path for e in volume.iterdir('/models',recursive=True)
               if e.type==FileEntryType.FILE and PurePosixPath(e.path).suffix=='.gguf']
    if remaining:
        raise RuntimeError('GGUF cache files remain after cleanup')
    write_json(output,{**record,'complete':True,'finished_at':now(),
                       'removed_bytes':sum(t['bytes'] for t in targets)})
    print(f"Removed {len(targets)} regenerable GGUF files; raw cloud outputs and manifests retained.")


if __name__=='__main__':
    main()
