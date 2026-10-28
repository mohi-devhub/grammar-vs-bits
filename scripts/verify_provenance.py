"""Verify shipped executed worker source against its original hash records."""
import hashlib
import json
from qunti.common import ROOT


def main():
    base=ROOT/'provenance/executed-workers'
    manifest=json.loads((base/'manifest.json').read_text())
    count=0
    for row in manifest['sessions']:
        record=json.loads((base/row['hash_record']).read_text())
        original=json.loads((ROOT/'results/ops'/(row['batch_id']+'_worker_source.json')).read_text())
        if record!=original:raise RuntimeError('Archived hash record differs from the original')
        for name,expected in record['sha256'].items():
            path=base/row['batch_id']/'qunti'/name
            if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise RuntimeError('Executed worker source mismatch: '+str(path.relative_to(ROOT)))
            count+=1
    print(f'Verified {count} executed source files across {len(manifest["sessions"])} archived model sessions.')


if __name__=='__main__':main()
