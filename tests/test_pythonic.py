import pytest
from qunti.pythonic import build_pythonic,parse_pythonic

def test_multiple_calls_literal_types_and_strings():
    assert parse_pythonic('[a.b(x=True,y=None,z={"k":[1,2.5]}),a.b(x=False)]')==[{'a.b':{'x':True,'y':None,'z':{'k':[1,2.5]}}},{'a.b':{'x':False}}]
    assert parse_pythonic('[]')==[]

@pytest.mark.parametrize('text',['f(x=1)','[f(1)]','[f(x=open("secret"))]','[f(**x)]','[f(x=1,x=2)]'])
def test_reject_execution_and_unsupported_envelopes(text):
    with pytest.raises((ValueError,SyntaxError)):parse_pythonic(text)

def test_grammar_uses_only_schema():
    grammar=build_pythonic([{'name':'a.b','parameters':{'type':'dict','properties':{'x':{'type':'boolean'}},'required':['x']}}])
    assert '"True" | "False"' in grammar and '"a.b"' in grammar
