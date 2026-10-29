"""Create a local reproducible release archive, excluding caches and credentials."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile
import tomllib
from qunti.common import ROOT, now, write_json

ROOTS = ['README.md', 'CITATION.cff', 'CHANGELOG.md', 'BUDGET.md', 'DECISIONS.md', 'LEARNING.md', 'AUDIT.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', '.gitignore', '.python-version',
         'pyproject.toml', 'uv.lock', 'requirements.lock', 'requirements-build.lock', 'requirements-analysis.lock',
         'cloud.py', 'full_cloud.py', 'pythonic_cloud.py', 'configs', 'data', 'docs', 'qunti', 'scripts', 'tests', 'results', 'figures', 'paper', 'provenance', 'third_party']
EXCLUDED_SUFFIXES = {'.pyc', '.gguf', '.safetensors', '.aux', '.out', '.bbl', '.blg'}
PATTERNS = [re.compile(rb'\bhf_[A-Za-z0-9]{20,}\b'), re.compile(rb'\b(?:ak|as)-[A-Za-z0-9_-]{20,}\b'),
            re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{20,}\b'), re.compile(rb'\bgithub_pat_[A-Za-z0-9_]{30,}\b')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    summary = json.loads((ROOT / 'results/full' / args.run_id / 'summary.json').read_text())
    if not summary['complete']:
        raise RuntimeError('Complete release requires the complete matrix frozen before execution')
    from scripts.verify_provenance import main as verify_sources
    verify_sources()
    files = []
    for name in ROOTS:
        root = ROOT / name
        candidates = root.rglob('*') if root.is_dir() else [root]
        for path in candidates:
            if path.is_symlink() or not path.is_file() or '__pycache__' in path.parts or path.suffix in EXCLUDED_SUFFIXES:
                continue
            if path.suffix=='.log' and 'paper' in path.relative_to(ROOT).parts:
                continue
            if path.name.startswith('.env') or any(p in ('.cache', '.venv', '.git') for p in path.relative_to(ROOT).parts):
                raise RuntimeError('Private path reached the release inventory')
            files.append(path)
    findings = []
    hashes = {}
    for path in sorted(files):
        contents = path.read_bytes()
        name = str(path.relative_to(ROOT))
        hashes[name] = hashlib.sha256(contents).hexdigest()
        if any(pattern.search(contents) for pattern in PATTERNS):
            findings.append(name)
    if findings:
        # Deliberately print paths only, never suspected credential values.
        raise RuntimeError('Credential-shaped strings require review in: ' + ', '.join(findings))
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    project=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']
    stem=f"{project['name']}-v{project['version']}-{args.run_id}"
    inventory = destination / (stem+'-files.json')
    write_json(inventory, {'project':project['name'],'version':project['version'],'run_id': args.run_id, 'files_sha256': hashes, 'credential_pattern_scan': 'passed',
                          'scope': 'First-party source, frozen inputs, raw/scored results, provenance, figures and manuscript. Runtime caches and model weights excluded.'})
    archive = destination / (stem+'.tar.gz')
    with archive.open('wb') as stream, gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|') as tar:
            for path, name in [(p, str(p.relative_to(ROOT))) for p in sorted(files)] + [(inventory, 'RELEASE_FILES.json')]:
                info = tar.gettarinfo(str(path), arcname='grammar-vs-bits/' + name)
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                info.mode = 0o644
                with path.open('rb') as source:
                    tar.addfile(info, source)
    write_json(destination / 'release.json', {'created_at': now(),'project':project['name'],'version':project['version'], 'run_id': args.run_id, 'archive': archive.name,'inventory':inventory.name,
               'bytes': archive.stat().st_size, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
               'inventoried_files': len(files), 'published': False})
    print(str(archive))


if __name__ == '__main__':
    main()
