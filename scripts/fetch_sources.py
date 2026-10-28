"""Fetch only pinned official archives, verify SHA-256, extract without links."""
import hashlib
import json
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath
from qunti.common import ROOT


def fetch(entry, destination, subtree=None):
    destination = ROOT / destination
    stamp = destination / '.qunti-source.json'
    if destination.exists():
        if stamp.exists() and json.loads(stamp.read_text()) == entry:
            print(f'Already present: {entry["name"]} {entry["commit"]}')
            return
        raise RuntimeError(f'{destination}: existing unstamped checkout; verify or move it first')
    url = f'https://codeload.github.com/{entry["repository"]}/tar.gz/{entry["commit"]}'
    destination.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        archive = Path(tmp) / 'source.tar.gz'
        with urllib.request.urlopen(url, timeout=120) as response, archive.open('wb') as out:
            shutil.copyfileobj(response, out)
        if hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest() != entry['archive_sha256']:
            raise RuntimeError('Official archive hash mismatch')
        unpacked = Path(tmp) / 'unpacked'
        unpacked.mkdir()
        with tarfile.open(archive) as tar:
            for member in tar:
                parts = PurePosixPath(member.name).parts[1:]
                if subtree:
                    if not parts or parts[0] != subtree:
                        continue
                    parts = parts[1:]
                if not parts:
                    continue
                if '..' in parts or member.issym() or member.islnk():
                    raise RuntimeError('Unsafe archive member')
                target = unpacked.joinpath(*parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as source, target.open('wb') as out:
                        shutil.copyfileobj(source, out)
        (unpacked / '.qunti-source.json').write_text(json.dumps(entry, indent=2) + '\n')
        unpacked.rename(destination)
    print(f'Fetched: {entry["name"]} {entry["commit"]}')


def main():
    runtime = json.loads((ROOT / 'docs/RUNTIME_SOURCES.json').read_text())[0]
    bfcl = json.loads((ROOT / 'docs/BFCL_SOURCE.json').read_text())
    fetch(runtime, 'vendor/llama.cpp')
    fetch(bfcl, 'vendor/bfcl', 'berkeley-function-call-leaderboard')


if __name__ == '__main__':
    main()
