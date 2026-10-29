"""Archive only the separate sensitivity's remote outputs and model manifests."""
import argparse,hashlib,json
from pathlib import PurePosixPath
import modal
from modal.types import FileEntryType
from qunti.common import ROOT,now,write_json
from scripts.pilot import app_snapshot


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='pythonic-002');args=p.parse_args()
    folder=ROOT/'results/sensitivity'/args.run_id;state=json.loads((folder/'state.json').read_text())
    if not state['complete']:raise RuntimeError('Finish or explicitly close collection before a final archive')
    if any(a['state']!='stopped' and a['description'].startswith(('grammar-vs-bits','qunti-check')) for a in app_snapshot()):raise RuntimeError('Our apps are still active')
    batches=[s['batch_id'] for s in state['sessions']]
    batches += [PurePosixPath(source).stem for s in state['sessions'] for source in s.get('continuation_sources',[])]
    volume=modal.Volume.from_name('qunti-check-artifacts',create_if_missing=False);inventory=[];entries=[]
    for batch in batches:
        entries.extend(e for e in volume.iterdir('/full/'+batch,recursive=True) if e.type==FileEntryType.FILE)
    for slug in ('Llama-3.2-1B-Instruct','Llama-3.2-3B-Instruct'):
        entries.extend(e for e in volume.iterdir('/models/'+slug) if e.type==FileEntryType.FILE and PurePosixPath(e.path).name=='manifest.json')
    for entry in entries:
        relative=PurePosixPath(entry.path.lstrip('/'))
        if '..' in relative.parts or relative.suffix in ('.gguf','.safetensors'):raise RuntimeError('Unexpected cache/unsafe path')
        target=folder/'cloud_archive'/str(relative);target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_suffix(target.suffix+'.download')
        with temporary.open('wb') as stream:volume.read_file_into_fileobj(entry.path,stream)
        if temporary.stat().st_size!=entry.size:raise RuntimeError('Archive size mismatch')
        with temporary.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        temporary.replace(target);inventory.append({'remote_path':entry.path,'local_path':str(target.relative_to(ROOT)),'bytes':entry.size,'sha256':sha})
    write_json(folder/'cloud_archive.json',{'date':now(),'complete':True,'volume':'qunti-check-artifacts','inventory':inventory,'deletion_performed':False})
    print(f'Archived {len(inventory)} sensitivity files without altering the primary archive.')

if __name__=='__main__':main()
