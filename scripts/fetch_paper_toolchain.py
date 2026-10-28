"""Fetch the pinned official TinyTeX archive into this repository only."""
import hashlib
import json
import tarfile
import urllib.request
from qunti.common import ROOT, write_json


def main():
    metadata=json.loads((ROOT/'docs/PAPER_TOOLCHAIN.json').read_text())
    target=ROOT/'.cache/paper-tex';target.mkdir(parents=True,exist_ok=True)
    archive=target/metadata['asset']
    if not archive.exists():
        temporary=archive.with_suffix('.download')
        with urllib.request.urlopen(metadata['url'],timeout=90) as response,temporary.open('wb') as out:
            while block:=response.read(1024*1024):out.write(block)
        temporary.replace(archive)
    with archive.open('rb') as source:
        actual=hashlib.file_digest(source,'sha256').hexdigest()
    if actual!=metadata['sha256']:raise RuntimeError('Official TeX archive SHA-256 mismatch')
    marker=target/'verified_source.json'
    if not marker.exists():
        with tarfile.open(archive) as source:source.extractall(target,filter='data')
        write_json(marker,{'source':metadata,'archive_sha256':actual,'global_install':False})
    if not (target/'TinyTeX/bin/universal-darwin/pdflatex').is_file():
        raise RuntimeError('Pinned archive does not contain the expected macOS pdflatex')
    print('Official pinned TeX archive verified; repo-local toolchain available.')


if __name__=='__main__':main()
