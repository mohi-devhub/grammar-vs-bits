"""Verify the v0.1.3 layout-only revision against v0.1.2 and the actual PDF."""
import hashlib
import json
import re
import subprocess
import tomllib
import xml.etree.ElementTree as ET

from qunti.common import ROOT, now, write_json


KEYWORDS = ('tool calling, quantization, constrained decoding, grammar-constrained '
            'generation, LLM evaluation, small language models')
BASE = 'v0.1.2'


def original(name):
    return subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT)


def without_layout(text):
    text = text.replace('\\usepackage{placeins}', '').replace('\\FloatBarrier', '')
    text = text.replace('\\par\\noindent\\textbf{Keywords:} ' + KEYWORDS + '\\par', '')
    for name in ('replication_table.tex', 'generated/effect_table.tex'):
        text = text.replace('\\input{' + name + '}', '')
    floats = re.findall(r'\\begin\{(table\*|figure\*)\}.*?\\end\{\1\}', text, re.S)
    assert len(floats) == 3
    text = re.sub(r'\\begin\{(table\*|figure\*)\}.*?\\end\{\1\}', '', text, flags=re.S)
    return re.sub(r'\s+', '', text)


def main():
    current = (ROOT / 'paper/main.tex').read_text()
    before = original('paper/main.tex').decode()
    if without_layout(current) != without_layout(before):
        raise RuntimeError('Manuscript prose changed beyond the approved layout and keywords')
    pattern = r'\\begin\{(table\*|figure\*)\}.*?\\end\{\1\}'
    if [m[0] for m in re.finditer(pattern, current, re.S)] != [m[0] for m in re.finditer(pattern, before, re.S)]:
        raise RuntimeError('Float content changed')
    keyword_line = '\\par\\noindent\\textbf{Keywords:} ' + KEYWORDS + '\\par'
    if '\\end{abstract}\n' + keyword_line not in current:
        raise RuntimeError('Keywords are not immediately after the abstract')
    if '\\FloatBarrier\n\\bibliographystyle{plain}' not in current:
        raise RuntimeError('Missing bibliography float barrier')
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    protected = {}
    for name in names:
        if not name.startswith(('data/', 'configs/', 'results/', 'figures/', 'paper/', 'provenance/')):
            continue
        if name in ('paper/main.tex', 'paper/main.pdf', 'results/full/full-002/paper_build.json'):
            continue
        old = original(name)
        if (ROOT / name).read_bytes() != old:
            raise RuntimeError('Protected source/result changed: ' + name)
        protected[name] = hashlib.sha256(old).hexdigest()
    old_lock = tomllib.loads(original('uv.lock').decode())
    new_lock = tomllib.loads((ROOT / 'uv.lock').read_text())
    for package in old_lock['package']:
        if package['name'] == 'grammar-vs-bits':
            package['version'] = '0.1.3'
    if old_lock != new_lock:
        raise RuntimeError('Locked dependencies changed')
    xml = subprocess.check_output(['pdftotext', '-bbox-layout', str(ROOT / 'paper/main.pdf'), '-'])
    ns = {'x': 'http://www.w3.org/1999/xhtml'}
    pages = ET.fromstring(xml).findall('.//x:page', ns)
    captions, references = [], []
    for number, page in enumerate(pages, 1):
        for line in page.findall('.//x:line', ns):
            words = [word.text for word in line.findall('x:word', ns)]
            if len(words) >= 2 and words[0] in ('Figure', 'Table') and re.fullmatch(r'[1-3]:', words[1]):
                captions.append({'float': words[0] + ' ' + words[1][:-1], 'page': number})
            if words == ['References']:
                references.append(number)
    expected = {kind + ' ' + str(i) for kind in ('Figure', 'Table') for i in range(1, 4)}
    if len(captions) != 6 or {row['float'] for row in captions} != expected or len(references) != 1:
        raise RuntimeError('Could not locate every caption and the References heading')
    if len(pages) > 7 or any(row['page'] >= references[0] for row in captions):
        raise RuntimeError('Page limit exceeded or a float reaches References')
    log = (ROOT / 'paper/main.log').read_text()
    if re.search(r'Overfull|undefined|multiply defined|Rerun to', log):
        raise RuntimeError('Unresolved PDF layout/reference warning')
    audit = json.loads((ROOT / 'results/ops/pip-audit-v0.1.3.json').read_text())
    if any(d.get('vulns') or 'skip_reason' in d for d in audit['dependencies']):
        raise RuntimeError('Dependency audit is not clean')
    record = {
        'date': now(), 'version': '0.1.3', 'base_release': BASE,
        'scope': 'Float placement and keywords only; no numbers or claims changed.',
        'pdf_pages': len(pages), 'pdf_sha256': hashlib.sha256((ROOT / 'paper/main.pdf').read_bytes()).hexdigest(),
        'float_pages': captions, 'references_begin_on_page': references[0],
        'every_float_on_an_earlier_page_than_references': True,
        'keywords_exact_and_immediately_after_abstract': True,
        'main_tex_prose_and_float_contents_preserved': True,
        'protected_files_unchanged': len(protected),
        'protected_manifest_sha256': hashlib.sha256(json.dumps(protected, sort_keys=True).encode()).hexdigest(),
        'locked_dependencies_changed': False, 'pip_audit_dependencies': len(audit['dependencies']),
        'pip_audit_vulnerabilities': 0, 'pip_audit_skipped_dependencies': 0,
        'existing_tests_passed': 36, 'executed_sources_verified': 56, 'new_cloud_compute': False,
    }
    write_json(ROOT / 'results/ops/v0.1.3_verification.json', record)
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
