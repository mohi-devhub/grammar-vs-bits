"""Package a tagged manuscript and verify a fresh pdflatex-only build."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import tomllib
import zipfile
import zlib

from PIL import Image

from qunti.common import ROOT


ARCHIVE = 'grammar-vs-bits-arxiv.zip'
SECRET_PATTERNS = [
    rb'\bhf_[A-Za-z0-9]{20,}\b', rb'\b(?:ak|as)-[A-Za-z0-9_-]{20,}\b',
    rb'\bgh[pousr]_[A-Za-z0-9]{20,}\b', rb'\bgithub_pat_[A-Za-z0-9_]{30,}\b',
    rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
]
PATH_PATTERN = rb'(?:/Users/|/home/|/tmp/|/private/var/|/var/folders/|/Volumes/|file://|[A-Za-z]:\\Users\\)'
NOTE_PATTERN = rb'(?i)(?:\bTODO\b|\bFIXME\b|NOTE TO SELF|PRIVATE NOTE|DO NOT SHARE)'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def released(name, ref):
    return subprocess.check_output(['git', 'show', ref + ':' + name], cwd=ROOT)


def comments(text):
    for line_number, line in enumerate(text.splitlines(keepends=True), 1):
        for match in re.finditer('%', line):
            prefix = line[:match.start()]
            slashes = len(prefix) - len(prefix.rstrip('\\'))
            if slashes % 2 == 0:
                yield line_number, match.start()
                break


def strip_comments(text):
    # This frozen manuscript has only a full-line generated-file comment.
    # Refuse inline comments rather than silently change TeX whitespace.
    locations = dict(comments(text))
    output = []
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        if number not in locations:
            output.append(line)
        elif line[:locations[number]].strip():
            raise ValueError('Inline TeX comment needs whitespace-preserving handling')
    result = ''.join(output)
    if not result.strip():
        result = '\\relax\n'
    return result, len(locations)


def public_check(name, data):
    chunks = [data]
    if name.endswith('.pdf'):
        for stream in re.finditer(rb'stream\r?\n(.*?)\r?\nendstream', data, re.S):
            try:
                chunks.append(zlib.decompress(stream[1]))
            except zlib.error:
                pass
    for chunk in chunks:
        for category, patterns in [('credential', SECRET_PATTERNS),
                                   ('machine-local path', [PATH_PATTERN]),
                                   ('private note', [NOTE_PATTERN])]:
            if any(re.search(pattern, chunk) for pattern in patterns):
                raise RuntimeError(f'Public-source scan failed in {name}: {category}')
    if name.endswith(('.tex', '.bbl', '.sty')):
        text = data.decode('utf-8')
        if list(comments(text)):
            raise RuntimeError('Unstripped TeX comment in ' + name)
        if re.search(r'\\(?:iffalse|todo|marginpar|pdfcomment)\b|\\begin\{comment\}', text):
            raise RuntimeError('Hidden or editorial TeX content in ' + name)


def payload(ref):
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', ref], cwd=ROOT, text=True).splitlines()
    selected = [name for name in names if name.startswith('paper/') and (
        name.endswith('.tex') or name.endswith('.sty'))]
    output = {}
    removed = 0
    for source in selected:
        name = str(PurePosixPath(source).relative_to('paper'))
        text = released(source, ref).decode('utf-8')
        if name == 'main.tex':
            text = text.replace('{../figures/', '{figures/')
            text = text.replace('\\bibliographystyle{plain}\n', '')
            text = text.replace('\\bibliography{references}', '\\input{main.bbl}')
        text, count = strip_comments(text)
        removed += count
        output[name] = text.encode('utf-8')
    bibliography = ROOT / 'paper/main.bbl'
    if not bibliography.is_file():
        raise RuntimeError('The compiled main.bbl must exist before packaging')
    text, count = strip_comments(bibliography.read_text())
    output['main.bbl'] = text.encode('utf-8')
    removed += count
    figures = sorted(set(re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', output['main.tex'].decode())))
    for name in figures:
        output[name] = released(name, ref)
    for name, data in output.items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or any(part.startswith('.') for part in path.parts):
            raise RuntimeError('Nonportable archive member')
        public_check(name, data)
        if name.endswith(('.tex', '.bbl', '.sty')):
            for target in re.findall(r'\\(?:input|include|includegraphics)(?:\[[^]]*\])?\{([^}]+)\}', data.decode()):
                candidate = target if PurePosixPath(target).suffix else target + '.tex'
                if candidate not in output:
                    raise RuntimeError(f'Unpackaged dependency in {name}: {candidate}')
    return output, removed, figures


def zip_bytes(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return stream.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', help='Git tag or commit; defaults to the project version tag')
    args = parser.parse_args()
    ref = args.ref or 'v' + tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']['version']
    version = tomllib.loads(released('pyproject.toml', ref).decode())['project']['version']
    tag = 'v' + version
    toolchain = (ROOT / '.cache/paper-tex').resolve()
    binary = toolchain / 'TinyTeX/bin/universal-darwin/pdflatex'
    if not binary.is_file():
        raise RuntimeError('Install the hash-pinned paper toolchain first')
    files, removed, figures = payload(ref)
    packed = zip_bytes(files)
    reference = released('paper/main.pdf', ref)
    verification = json.loads(released('results/ops/' + tag + '_verification.json', ref))
    if sha(reference) != verification['pdf_sha256']:
        raise RuntimeError('Released reference PDF checksum mismatch')
    command = ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', '-no-shell-escape', '-recorder', 'main.tex']
    with tempfile.TemporaryDirectory(prefix='grammar-vs-bits-arxiv-') as temporary:
        workspace = Path(temporary).resolve()
        clean = workspace / 'clean'
        clean.mkdir()
        with zipfile.ZipFile(io.BytesIO(packed)) as archive:
            if archive.testzip() is not None:
                raise RuntimeError('ZIP CRC verification failed')
            archive.extractall(clean)
        if {str(p.relative_to(clean)) for p in clean.rglob('*') if p.is_file()} != set(files):
            raise RuntimeError('Fresh extraction contains unexpected files')
        environment = dict(os.environ)
        for key in ('TEXINPUTS', 'BIBINPUTS', 'BSTINPUTS', 'TEXMFOUTPUT', 'TEXMFCNF'):
            environment.pop(key, None)
        for key, suffix in [('TEXMFVAR', 'var'), ('TEXMFCONFIG', 'config')]:
            state = workspace / suffix
            state.mkdir()
            environment[key] = str(state)
        # This contains pinned official TeX packages, not project styles.
        environment['TEXMFHOME'] = str(toolchain / 'home')
        environment['openin_any'] = 'p'
        environment['openout_any'] = 'p'
        for _ in range(3):
            result = subprocess.run([str(binary), *command[1:]], cwd=clean, env=environment,
                                    capture_output=True, text=True, timeout=120)
            if result.returncode:
                raise RuntimeError('Clean pdflatex build failed:\n' + result.stdout[-2500:])
        log = (clean / 'main.log').read_text()
        if re.search(r'Overfull|undefined|multiply defined|Rerun to', log):
            raise RuntimeError('Clean build has unresolved layout/reference warnings')
        page_match = re.search(r'Output written on main.pdf \((\d+) pages', log)
        page_count = int(page_match[1]) if page_match else 0
        if page_count != verification['pdf_pages']:
            raise RuntimeError('Clean build page count differs from the release')
        project_inputs = set()
        for line in (clean / 'main.fls').read_text().splitlines():
            if not line.startswith('INPUT '):
                continue
            path = Path(line[6:])
            path = (clean / path).resolve() if not path.is_absolute() else path.resolve()
            if path.is_relative_to(ROOT) and not path.is_relative_to(toolchain):
                raise RuntimeError('Clean build read an original project file')
            if path.is_relative_to(clean) and str(path.relative_to(clean)) in files:
                project_inputs.add(str(path.relative_to(clean)))
        if project_inputs != set(files):
            raise RuntimeError('Archive includes unused typesetting inputs: ' + ', '.join(sorted(set(files) - project_inputs)))
        reference_path = workspace / 'released.pdf'
        reference_path.write_bytes(reference)
        built_path = clean / 'main.pdf'
        text = subprocess.check_output(['pdftotext', '-layout', str(built_path), '-'])
        if text != subprocess.check_output(['pdftotext', '-layout', str(reference_path), '-']):
            raise RuntimeError('Clean PDF text differs from ' + tag)
        urls = lambda path: set(re.findall(r'https?://\S+', subprocess.check_output(['pdfinfo', '-url', str(path)], text=True)))
        if urls(built_path) != urls(reference_path):
            raise RuntimeError('Clean PDF link targets differ from the release')
        pages = []
        for label, pdf in [('released', reference_path), ('clean', built_path)]:
            subprocess.run(['pdftoppm', '-r', '150', '-png', str(pdf), str(workspace / label)],
                           check=True, capture_output=True, timeout=120)
        for page in range(1, page_count + 1):
            with Image.open(workspace / f'released-{page}.png') as original, Image.open(workspace / f'clean-{page}.png') as built:
                original = original.convert('RGB')
                built = built.convert('RGB')
                if original.size != built.size or original.tobytes() != built.tobytes():
                    raise RuntimeError(f'Clean PDF pixels differ on page {page}')
                pages.append({'page': page, 'pixel_dimensions': list(built.size), 'pixels_sha256': sha(built.tobytes()), 'different_pixels': 0})
        rebuilt = built_path.read_bytes()
        public_check('rebuilt-main.pdf', rebuilt)
    destination = ROOT / 'arxiv'
    destination.mkdir(exist_ok=True)
    (destination / ARCHIVE).write_bytes(packed)
    (destination / 'main.pdf').write_bytes(rebuilt)
    (destination / (ARCHIVE + '.sha256')).write_text(sha(packed) + '  ' + ARCHIVE + '\n')
    record = {
        'date': datetime.now(timezone.utc).isoformat(), 'release': tag,
        'source_commit': subprocess.check_output(['git', 'rev-parse', ref + '^{commit}'], cwd=ROOT, text=True).strip(),
        'archive': ARCHIVE, 'archive_sha256': sha(packed), 'archive_bytes': len(packed),
        'files_sha256': {name: sha(data) for name, data in sorted(files.items())},
        'compiled_bibliography_included': True, 'all_referenced_figures': figures,
        'local_styles': [name for name in files if name.endswith('.sty')],
        'tex_comments_removed': removed, 'tex_comments_remaining': 0,
        'credential_local_path_and_private_note_scan': 'passed, including decompressed PDF streams',
        'only_contained_relative_project_references': True,
        'fresh_extraction_compiles': True, 'command': command, 'pdflatex_passes': 3,
        'bibtex_invoked': False, 'shell_escape': False, 'original_project_inputs_read': False,
        'standard_toolchain': subprocess.check_output([str(binary), '--version'], text=True).splitlines()[0],
        'pages': page_count, 'release_pdf_sha256': sha(reference), 'rebuilt_pdf_sha256': sha(rebuilt),
        'pdf_bytes_identical': reference == rebuilt, 'extracted_text_identical': True,
        'external_link_targets_identical': True,
        'render_dpi': 150, 'all_pages_pixel_identical': True, 'page_comparisons': pages,
        'packaging_changes': ['Contained figure paths', 'Direct compiled-bibliography include', 'Strip comments; comment-only macros include becomes a no-op'],
        'excluded': ['Unused PNG/SVG plot exports', 'Briefing and practice script', 'Audits and working notes', 'Bibliography database', 'Logs, auxiliary files, JSON provenance, credentials and caches'],
        'official_source_guidance': 'https://info.arxiv.org/help/submit_tex.html',
    }
    (destination / 'VALIDATION.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f'Created arxiv/{ARCHIVE}: {len(files)} source files, clean pdflatex-only build, {page_count} pages.')
    print(f'Extracted text and all rendered page pixels match {tag}; public-source scans passed.')


if __name__ == '__main__':
    main()
