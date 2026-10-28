import pytest
from qunti.full_runner import decoding,trigger_probes
from qunti import full_runner


def test_native_trigger_modes_and_free_contract():
    item={'grammars':{'loose':'loose','trigger_strict':'trigger','whole_strict':'strict'}}
    assert decoding(item,'free','qwen')=={}
    assert decoding(item,'whole_strict','qwen')=={'grammar':'strict','grammar_lazy':False}
    assert decoding(item,'trigger_strict','qwen')['grammar_triggers']==[{'type':1,'value':'<tool_call>'}]
    assert decoding(item,'trigger_strict','llama')['grammar_triggers']==[{'type':2,'value':r'(\[|\{)'}]
    assert decoding(item,'trigger_strict','qwen')['preserved_tokens']==['<tool_call>']
    assert 'preserved_tokens' not in decoding(item,'trigger_strict','llama')


def test_trigger_preflight_detects_unenforced_api(monkeypatch):
    def response(path,data):
        if path=='/tokenize':return {'tokens':[42]}
        return {'content':'unconstrained prose','generation_settings':{'grammar_lazy':False},'stop_type':'eos'}
    monkeypatch.setattr(full_runner,'request',response)
    assert not trigger_probes('qwen')[0]['passed']


def test_native_llama_prompt_keeps_one_bos_as_token_ids(monkeypatch):
    def tokenize(path,body):
        return {'tokens':[128000,128000,128006] if body['add_special'] else [128000,128006]}
    monkeypatch.setattr(full_runner,'request',tokenize)
    prompt,tokens=full_runner.native_prompt('<|begin_of_text|><|start_header_id|>','llama')
    assert isinstance(prompt,list) and prompt==tokens==[128000,128006]


def test_real_lazy_replay_error_counts_as_failure_without_suppressing_other_errors():
    body='{"error":{"code":500,"message":"got exception: Unexpected empty grammar stack after accepting piece: []"}}'
    assert full_runner.http_failure_status('trigger_strict',500,body)=='grammar_trigger_replay_error'
    assert full_runner.http_failure_status('free',500,body)=='request_error'
    assert full_runner.http_failure_status('trigger_strict',503,'unavailable')=='request_error'
