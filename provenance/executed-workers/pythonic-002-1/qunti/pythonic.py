"""Pythonic call-list grammar and AST-only scoring. Never execute generated calls."""
import ast
import json
import keyword
from qunti.grammar import Compiler,UnsupportedSchema,literal,normalize

class PythonicCompiler(Compiler):
    def __init__(self):
        super().__init__()
        self.rules['boolean']='"True" | "False"'
        self.rules['null']='"None"'
        self.rules['string']=(r'''"\"" ([^"\\\x00-\x1F] | "\\" (["'\\abfnrtv] | "u" [0-9a-fA-F]{4} | "x" [0-9a-fA-F]{2}))* "\""'''
                              +' | '+r'''"'" ([^'\\\x00-\x1F] | "\\" (["'\\abfnrtv] | "u" [0-9a-fA-F]{4} | "x" [0-9a-fA-F]{2}))* "'"''')
    def compile(self,schema):
        if 'enum' in schema or 'const' in schema:
            values=[schema['const']] if 'const' in schema else schema['enum']
            if not values:raise UnsupportedSchema('Empty enum')
            name=self.name();self.rules[name]=' | '.join(literal(repr(v)) for v in values)
            return name
        name=super().compile(schema)
        normalized=normalize(schema)
        if normalized.get('type')=='object':
            for key in normalized.get('properties',{}):
                quoted=literal(json.dumps(key,ensure_ascii=True))
                either='('+quoted+' | '+literal(repr(key))+')'
                for rule in list(self.rules):
                    if rule.startswith(name+'-s-'):
                        self.rules[rule]=self.rules[rule].replace(quoted,either)
        return name
    def kwargs(self,schema):
        schema=normalize(schema);props=schema.get('properties',{});names=list(props)
        if len(names)>12:raise UnsupportedSchema('Too many argument order states')
        if any(not n.isidentifier() or keyword.iskeyword(n) for n in names):
            raise UnsupportedSchema('Argument is not a Python keyword identifier')
        prefix=self.name();required=set(schema.get('required',[]))
        needed=sum(1<<i for i,k in enumerate(names) if k in required)
        children=[self.compile(props[n]) for n in names]
        for mask in range(1<<len(names)):
            choices=['""'] if mask&needed==needed else []
            for i,name in enumerate(names):
                if mask&(1<<i):continue
                comma='ws "," ws ' if mask else ''
                choices.append(comma+literal(name)+' ws "=" ws '+children[i]+f' {prefix}-{mask|(1<<i)}')
            self.rules[f'{prefix}-{mask}']=' | '.join(choices)
        return prefix+'-0'

def build_pythonic(tools):
    c=PythonicCompiler();calls=[]
    for tool in tools:
        if any(not p.isidentifier() or keyword.iskeyword(p) for p in tool['name'].split('.')):
            raise UnsupportedSchema('Tool name is not a Python dotted identifier')
        calls.append(literal(tool['name'])+' ws "(" ws '+c.kwargs(tool['parameters'])+' ws ")"')
    c.rules['call']=' | '.join('('+s+')' for s in calls)
    return c.emit('ws "[" ws (call (ws "," ws call)*)? ws "]" ws')

def parse_pythonic(text):
    node=ast.parse(text.strip(),mode='eval').body
    if not isinstance(node,ast.List):raise ValueError('Expected a Python list of calls')
    def name(n):
        if isinstance(n,ast.Name):return n.id
        if isinstance(n,ast.Attribute):return name(n.value)+'.'+n.attr
        raise ValueError('Unsupported callable expression')
    calls=[]
    for call in node.elts:
        if not isinstance(call,ast.Call) or call.args:raise ValueError('Expected keyword-argument calls')
        args={}
        for kw in call.keywords:
            if kw.arg is None or kw.arg in args:raise ValueError('Unpacked or duplicate argument')
            args[kw.arg]=ast.literal_eval(kw.value)
        calls.append({name(call.func):args})
    return calls

def score_pythonic(item,text,completed=True):
    from qunti.scoring import official
    from jsonschema import Draft202012Validator
    try:calls=parse_pythonic(text)
    except (ValueError,SyntaxError,TypeError,RecursionError) as exc:
        return {'correct':False,'format_valid':False,'schema_valid':False,'parse_error':str(exc)}
    offered={t['name']:t for t in item['input']['function']};valid=True
    for call in calls:
        fn,args=next(iter(call.items()))
        valid &= fn in offered and not list(Draft202012Validator(normalize(offered[fn]['parameters'])).iter_errors(args))
    checker,language=official()
    result=checker(item['input']['function'],calls,item['expected'],language,item['source_category'],'qunti-check') if completed else None
    return {'correct':bool(result and result['valid']),'format_valid':True,'schema_valid':bool(valid),'official':result}
