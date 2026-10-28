"""Freeze and validate the separately authorized Pythonic sensitivity."""
import json,random,subprocess,tempfile
from transformers import AutoTokenizer
from qunti.common import ROOT,digest,now,read_jsonl,write_json
from qunti.grammar import example
from qunti.pythonic import build_pythonic,parse_pythonic

def main():
    folder=ROOT/'data/pythonic';folder.mkdir(parents=True,exist_ok=True)
    originals=[r for r in read_jsonl(ROOT/'data/frozen.jsonl') if r['category']=='parallel']
    upstream=ROOT/'vendor/bfcl/bfcl_eval/data/BFCL_v4_parallel_multiple.json'
    chosen=random.Random('20261027:parallel_multiple').sample(sorted(read_jsonl(upstream),key=lambda r:r['id']),60)
    answers={r['id']:r['ground_truth'] for r in read_jsonl(upstream.parent/'possible_answer'/upstream.name)}
    items=originals+[{'id':r['id'],'category':'parallel_multiple','source_category':'parallel_multiple','input':r,'expected':answers[r['id']],'input_sha256':digest(r)} for r in chosen]
    items.sort(key=lambda r:(r['category'],r['id']))
    frozen=folder/'frozen.jsonl';contents=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in items)
    if frozen.exists() and frozen.read_text()!=contents:raise RuntimeError('Refuse to change frozen items')
    frozen.write_text(contents)
    base=json.loads((ROOT/'configs/protocol.json').read_text())
    protocol={**base,'stage':'full','arms':['free','whole_strict'],'full_run_generations':4800,'output_contract':'pythonic_list',
              'trigger_preflight':False,'sensitivity_only':True,'items_per_model':120,'optional_spend_cap_usd':3,
              'execution':{**base['execution'],'gpu_deadline_seconds':2500}}
    write_json(ROOT/'configs/pythonic_protocol.json',protocol)
    specs=[r for r in json.loads((ROOT/'configs/full_models.json').read_text()) if r['family']=='llama']
    validator=ROOT/'.cache/llama-build/bin/test-gbnf-validator';checks=[]
    for item in items:
        path=folder/(item['id']+'.gbnf');path.write_text(build_pythonic(item['input']['function']))
        witnesses=[t['name']+'('+', '.join(k+'='+repr(v) for k,v in example(t['parameters']).items())+')' for t in item['input']['function']]
        cases=[('empty','[]',True),('parallel','['+', '.join(witnesses[:1]*2)+']',True),('unknown','[__not_offered__()]',False),('json','{"name":"tool"}',False),('prose','I will call it.',False)]
        cases += [('witness:'+str(i),'['+call+']',True) for i,call in enumerate(witnesses)]
        for label,text,expected in cases:
            with tempfile.NamedTemporaryFile('w') as stream:
                stream.write(text);stream.flush()
                r=subprocess.run([str(validator),str(path),stream.name],capture_output=True,text=True,timeout=15)
            actual=r.stdout.startswith('Input string is valid according to the grammar.')
            checks.append({'id':item['id'],'case':label,'passed':r.returncode==0 and actual==expected,'expected':expected,'actual':actual})
            if expected:parse_pythonic(text)
    write_json(ROOT/'results/offline/pythonic_validation.json',{'date':now(),'cases':len(checks),'failed':sum(not r['passed'] for r in checks),'checks':checks,'no_model_loaded':True,'validator_sha256':digest(validator.read_bytes())})
    if any(not r['passed'] for r in checks):raise RuntimeError('Grammar gate failed')
    for spec in specs:
        tokenizer=AutoTokenizer.from_pretrained(ROOT/'.cache/full-tokenizers'/spec['slug'],local_files_only=True,trust_remote_code=False)
        requests=[]
        for item in items:
            system=('Use the supplied function definitions to answer the user request. Return only a Python list of calls, '
                    'for example [tool_name(argument=value)]. Include every needed call. If no offered function applies, return []. '
                    'Do not include prose or markdown. Functions:\n'+json.dumps(item['input']['function'],ensure_ascii=False,indent=2))
            prompt=tokenizer.apply_chat_template([{'role':'system','content':system}]+item['input']['question'][0],tokenize=False,add_generation_prompt=True,date_string='27 Oct 2026')
            assert 'Respond in the format {"name": function name' not in prompt
            requests.append({'id':item['id'],'category':item['category'],'prompt':prompt,'input_sha256':item['input_sha256'],'schema_sha256':digest(item['input']['function']),'grammars':{'whole_strict':(folder/(item['id']+'.gbnf')).read_text()}})
        write_json(folder/(spec['slug']+'.json'),requests)
    write_json(folder/'manifest.json',{'frozen_at':now(),'items':120,'categories':{'parallel':60,'parallel_multiple':60},'selection_seed':20261027,
        'selection':'Original 60 parallel cases plus sorted parallel_multiple pool sampled with Random("20261027:parallel_multiple"); no outcome filtering.',
        'frozen_sha256':digest(frozen.read_bytes()),'new_upstream_sha256':digest(upstream.read_bytes()),'models':specs,
        'source':'https://github.com/meta-llama/llama-models/blob/0e0b8c519242d5833d8c11bffc1232b77ad7f301/models/llama3_2/text_prompt_format.md',
        'prompt_scope':'Documented Pythonic call-list form; paraphrased instructions and study convention [] for abstention. tools= omitted to avoid single-object JSON injection. Joint prompt/parser/grammar sensitivity, not a parser-only intervention.',
        'baseline_comparison':'Only the original 60 parallel items have a matched primary JSON baseline; parallel_multiple is a separate endpoint.'})
    print(f'Frozen 120 sensitivity cases; {len(checks)} C++ membership checks passed. No cloud work launched.')

if __name__=='__main__':main()
