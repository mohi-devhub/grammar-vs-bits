"""Freeze all generation inputs from publisher tokenizers and offered schemas only."""
import json
from pathlib import Path
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer
from qunti.common import ROOT, read_jsonl, write_json, digest
from qunti.grammar import normalize

SPECS=[
 {'model':'Qwen/Qwen3-0.6B','revision':'c1899de289a04d12100db370d81485cdf75e47ca','slug':'Qwen3-0.6B','family':'qwen'},
 {'model':'meta-llama/Llama-3.2-1B-Instruct','revision':'9213176726f574b556790deb65791e0c5aa438b6','slug':'Llama-3.2-1B-Instruct','family':'llama'},
 {'model':'meta-llama/Llama-3.2-3B-Instruct','revision':'0cb88a4f764b7a12671c53f0838cd831a0843b95','slug':'Llama-3.2-3B-Instruct','family':'llama'}]


def main():
    items=read_jsonl(ROOT/'data/frozen.jsonl')
    for spec in SPECS:
        local=snapshot_download(spec['model'],revision=spec['revision'],
            allow_patterns=['config.json','tokenizer*.json','tokenizer*.jinja','chat_template*.jinja'],
            local_dir=str(ROOT/'.cache/full-tokenizers'/spec['slug']))
        tokenizer=AutoTokenizer.from_pretrained(local,trust_remote_code=False)
        native=('output each call as <tool_call>{"name":"function_name","arguments":{...}}</tool_call>. You may emit multiple such blocks when the request needs multiple calls.'
                if spec['family']=='qwen' else 'output a JSON object {"name":"function_name","parameters":{...}}. If multiple calls are needed, output a JSON array of these call objects.')
        system=('You are a tool-calling assistant. Use only the offered functions and documented arguments. When one or more tools apply, '+native+
                ' If none applies, output exactly NO_CALL. Do not add prose, markdown, or reasoning.')
        out=[]
        for item in items:
            tools=[{'type':'function','function':{**t,'parameters':normalize(t['parameters'])}} for t in item['input']['function']]
            messages=[{'role':'system','content':system}]+item['input']['question'][0]
            prompt=tokenizer.apply_chat_template(messages,tools=tools,tokenize=False,add_generation_prompt=True,
                                                enable_thinking=False,date_string='27 Oct 2026')
            out.append({'id':item['id'],'category':item['category'],'prompt':prompt,'input_sha256':item['input_sha256'],
                        'schema_sha256':digest(tools),'grammars':{arm:(ROOT/'data/grammars'/spec['family']/arm/(item['id']+'.gbnf')).read_text()
                                                               for arm in ('loose','trigger_strict','whole_strict')}})
        assert len(out)==200
        write_json(ROOT/'data/full_requests'/(spec['slug']+'.json'),out)
        write_json(ROOT/'results/ops'/(spec['slug']+'_full_tokenizer.json'),{**spec,'chat_template_sha256':digest(tokenizer.chat_template),
                   'prompt_bundle_sha256':digest([r['prompt'] for r in out]),'request_count':len(out),'date_string':'27 Oct 2026','gold_answers_used':False})
    write_json(ROOT/'configs/full_models.json',SPECS)
    print('Prepared 200 fixed requests for each model; no cloud compute launched.')


if __name__=='__main__':main()
