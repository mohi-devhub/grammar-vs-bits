"""Verify actual release bytes, notices and executed-source snapshots."""
import argparse,hashlib,json,tarfile
from qunti.common import ROOT,now,write_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);args=p.parse_args()
    folder=ROOT/'dist';release=json.loads((folder/'release.json').read_text())
    if release['run_id']!=args.run_id:raise RuntimeError('Wrong release ID')
    archive=folder/release['archive']
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=release['sha256']:raise RuntimeError('Archive checksum mismatch')
    expected=json.loads((folder/f'qunti-check-{args.run_id}-files.json').read_text());hashes=expected['files_sha256']
    required={'LICENSE','THIRD_PARTY_NOTICES.md','third_party/gorilla/LICENSE','third_party/gorilla/NOTICE.md','provenance/executed-workers/manifest.json','paper/main.pdf'}
    if not required<=hashes.keys():raise RuntimeError('Release lacks required licenses/provenance/manuscript')
    manifest=json.loads((ROOT/'provenance/executed-workers/manifest.json').read_text())
    for session in manifest['sessions']:
        base='provenance/executed-workers/'+session['batch_id']
        record=json.loads((ROOT/base/'SHA256.json').read_text())
        for path,sha in record['sha256'].items():
            if hashes.get(base+'/qunti/'+path)!=sha:raise RuntimeError('Executed source not included byte-for-byte')
    seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.startswith('qunti-check/'):raise RuntimeError('Unsafe archive entry')
            name=member.name[len('qunti-check/'):]
            if name in seen or '..' in name.split('/') or name.endswith(('.gguf','.safetensors')):raise RuntimeError('Duplicate/unsafe/weight entry')
            seen.add(name);stream=tar.extractfile(member)
            if name=='RELEASE_FILES.json':
                if json.load(stream)!=expected:raise RuntimeError('Embedded inventory mismatch')
            elif name not in hashes or hashlib.file_digest(stream,'sha256').hexdigest()!=hashes[name]:raise RuntimeError('Archive member checksum mismatch: '+name)
    if seen!=set(hashes)|{'RELEASE_FILES.json'}:raise RuntimeError('Missing archive member')
    for path,sha in hashes.items():
        with (ROOT/path).open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=sha:raise RuntimeError('Source changed after packaging: '+path)
    result={'date':now(),'archive_sha256':release['sha256'],'all_archive_and_working_file_hashes_match':True,
            'files_checked':len(hashes),'licenses_and_executed_sources_included':True,'credential_pattern_scan':expected['credential_pattern_scan'],'published':False}
    write_json(folder/'validation.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
