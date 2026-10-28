"""Build the manuscript locally with a verified repo-local TinyTeX installation."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from qunti.common import ROOT, now, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    provenance = json.loads((ROOT / 'paper/generated/provenance.json').read_text())
    if provenance['run_id'] != args.run_id:
        raise RuntimeError('Generated paper inputs belong to another run')
    binaries = ROOT / '.cache/paper-tex/TinyTeX/bin/universal-darwin'
    if not (binaries / 'pdflatex').is_file():
        raise RuntimeError('Install the official hash-verified TinyTeX artifact recorded in docs/PAPER_TOOLCHAIN.json into .cache/paper-tex first')
    environment = dict(os.environ)
    for key, suffix in [('TEXMFVAR', 'var'), ('TEXMFCONFIG', 'config'), ('TEXMFHOME', 'home')]:
        path = ROOT / '.cache/paper-tex' / suffix
        path.mkdir(exist_ok=True)
        environment[key] = str(path)
    # Figures live in the sibling figures directory; reading ../ is intentional.
    environment['openin_any'] = 'r'
    environment['openout_any'] = 'p'
    latex = [str(binaries / 'pdflatex'), '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', '-no-shell-escape', 'main.tex']
    commands = [latex, [str(binaries / 'bibtex'), 'main'], latex, latex]
    for index, command in enumerate(commands):
        result = subprocess.run(command, cwd=ROOT / 'paper', env=environment, capture_output=True, text=True, timeout=120)
        (ROOT / f'.cache/paper-build-{index}.log').write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f'Local paper build step {index} failed; see .cache/paper-build-{index}.log')
    log = (ROOT / 'paper/main.log').read_text()
    match = re.search(r'Output written on main.pdf \((\d+) pages?', log)
    if not match:
        raise RuntimeError('Could not establish actual PDF page count')
    pages = int(match.group(1))
    pdf = ROOT / 'paper/main.pdf'
    record = {'created_at': now(), 'run_id': args.run_id, 'pages': pages,
              'pdf_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
              'toolchain_source': 'docs/PAPER_TOOLCHAIN.json', 'shell_escape': False,
              'warnings': [line for line in log.splitlines() if any(x in line for x in ('Warning:', 'Overfull', 'Underfull'))]}
    write_json(ROOT / 'results/full' / args.run_id / 'paper_build.json', record)
    if pages not in range(4, 7):
        raise RuntimeError(f'Actual manuscript has {pages} pages; required length is 4–6 pages')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
