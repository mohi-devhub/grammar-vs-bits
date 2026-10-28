"""Schema-only GBNF; neither compilation nor examples accept a gold answer.

Objects use subset states to permit every documented-key ordering while enforcing
required/unique keys. Free-form dictionaries remain free-form. Closed documented
objects are a declared API policy, independent of benchmark answers.
"""
import copy
import json
from itertools import combinations


class UnsupportedSchema(ValueError):
    pass


def literal(text):
    return json.dumps(text, ensure_ascii=True)


def normalize(schema):
    out = copy.deepcopy(schema)
    types = {"dict": "object", "float": "number", "int": "integer", "list": "array", "tuple": "array", "bool": "boolean", "str": "string"}
    kind = out.get("type")
    if kind == "any":
        out.pop("type")
    elif isinstance(kind, str):
        out["type"] = types.get(kind, kind)
    for key in ("properties", "$defs", "definitions"):
        if key in out:
            out[key] = {k: normalize(v) for k, v in out[key].items()}
    if isinstance(out.get("items"), dict):
        out["items"] = normalize(out["items"])
    if out.get("type") == "object" and out.get("required"):
        # A BFCL nested dict can declare required names without property types.
        # Such names have an unconstrained value, not a guessed reference type.
        out.setdefault("properties", {})
        for name in out["required"]:
            out["properties"].setdefault(name, {})
    if out.get("type") == "object" and out.get("properties"):
        out["additionalProperties"] = False
    return out


class Compiler:
    def __init__(self):
        self.rules = {
            "ws": r'[ \t\n\r]*',
            "string": r'"\"" ([^"\\\x00-\x1F] | "\\" (["\\/bfnrt] | "u" [0-9a-fA-F]{4}))* "\""',
            "number": r'"-"? ("0" | [1-9] [0-9]*) ("." [0-9]+)? ([eE] [+-]? [0-9]+)?',
            "integer": r'"-"? ("0" | [1-9] [0-9]*)',
            "boolean": r'"true" | "false"',
            "null": r'"null"',
            "value": 'string | number | boolean | null | any-object | any-array',
            "any-object": r'"{" ws (string ws ":" ws value (ws "," ws string ws ":" ws value)*)? ws "}"',
            "any-array": r'"[" ws (value (ws "," ws value)*)? ws "]"',
        }
        self.serial = 0

    def name(self):
        self.serial += 1
        return f"node-{self.serial}"

    def compile(self, schema):
        schema = normalize(schema)
        allowed = {"type", "description", "title", "default", "examples", "optional", "properties", "required", "additionalProperties", "items", "enum", "const", "oneOf", "anyOf", "minItems", "maxItems"}
        unknown = set(schema) - allowed
        if unknown:
            raise UnsupportedSchema(f"Unsupported schema keywords: {sorted(unknown)}")
        name = self.name()
        if "const" in schema or "enum" in schema:
            values = [schema["const"]] if "const" in schema else schema["enum"]
            if not values:
                raise UnsupportedSchema("Empty enum")
            self.rules[name] = " | ".join(literal(json.dumps(v, ensure_ascii=True, separators=(",", ":"), allow_nan=False)) for v in values)
        elif "oneOf" in schema or "anyOf" in schema:
            self.rules[name] = " | ".join(self.compile(s) for s in schema.get("oneOf", schema.get("anyOf")))
        elif isinstance(schema.get("type"), list):
            self.rules[name] = " | ".join(self.compile({**schema, "type": t}) for t in schema["type"])
        elif schema.get("type") == "object":
            props = schema.get("properties", {})
            required = set(schema.get("required", []))
            if required - props.keys():
                raise UnsupportedSchema("Required key missing from properties")
            if not props:
                self.rules[name] = "any-object" if schema.get("additionalProperties", True) else r'"{" ws "}"'
                return name
            if len(props) > 12:
                raise UnsupportedSchema("Object needs more than 4096 order states; redesign before inference")
            names = list(props)
            fields = [(literal(json.dumps(k, ensure_ascii=True)), self.compile(props[k])) for k in names]
            needed = sum(1 << i for i, k in enumerate(names) if k in required)
            all_mask = (1 << len(names)) - 1
            for mask in range(all_mask + 1):
                choices = []
                if mask & needed == needed:
                    choices.append('""')
                for i, (key, value) in enumerate(fields):
                    if mask & (1 << i):
                        continue
                    comma = 'ws "," ws ' if mask else ""
                    choices.append(f'{comma}{key} ws ":" ws {value} {name}-s-{mask | (1 << i)}')
                self.rules[f"{name}-s-{mask}"] = " | ".join(choices) if choices else '""'
            self.rules[name] = f'"{{" ws {name}-s-0 ws "}}"'
        elif schema.get("type") == "array":
            child = self.compile(schema.get("items", {}))
            low, high = schema.get("minItems", 0), schema.get("maxItems")
            if not isinstance(low, int) or low < 0 or (high is not None and (not isinstance(high, int) or high < low)):
                raise UnsupportedSchema("Invalid array bounds")
            if high is not None:
                if high > 32:
                    raise UnsupportedSchema("Large fixed array bound")
                choices = [' ws "," ws '.join([child] * n) or '""' for n in range(low, high + 1)]
                inner = "(" + " | ".join(choices) + ")"
            elif low == 0:
                inner = f'({child} (ws "," ws {child})*)?'
            else:
                inner = ' ws "," ws '.join([child] * low) + f' (ws "," ws {child})*'
            self.rules[name] = f'"[" ws {inner} ws "]"'
        else:
            kind = schema.get("type")
            if kind not in (None, "string", "number", "integer", "boolean", "null"):
                raise UnsupportedSchema(f"Unsupported type: {kind}")
            self.rules[name] = kind or "value"
        return name

    def emit(self, root):
        return "\n".join([f"root ::= {root}"] + [f"{k} ::= {v}" for k, v in self.rules.items()]) + "\n"


def call_schema(tools, family="qwen"):
    arg_key = "arguments" if family == "qwen" else "parameters"
    return {"oneOf": [
        {"type": "object", "properties": {
            "name": {"const": t["name"]}, arg_key: normalize(t["parameters"])},
         "required": ["name", arg_key], "additionalProperties": False}
        for t in tools
    ]}


def build(tools, family="qwen", arm="whole_strict"):
    c = Compiler()
    body = c.compile(call_schema(tools, family))
    if family == "qwen":
        c.rules["call"] = f'{literal("<tool_call>")} ws {body} ws {literal("</tool_call>")}'
        strict = f'ws ({literal("NO_CALL")} | call (ws call)*) ws'
    else:
        c.rules["call"] = body
        strict = f'ws ({literal("NO_CALL")} | call | "[" ws call (ws "," ws call)* ws "]") ws'
    if arm == "loose":
        c.rules["unrestricted"] = ".*"
        c.rules["strict"] = strict
        return c.emit("strict | unrestricted")
    if arm == "trigger_strict":
        # llama.cpp replays the trigger against root when lazy mode activates.
        return c.emit('call (ws call)* ws' if family == "qwen" else strict)
    return c.emit(strict)


def example(schema):
    """Construct a schema witness from schema data only, never benchmark labels."""
    schema = normalize(schema)
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return schema["enum"][0]
    if "oneOf" in schema or "anyOf" in schema:
        return example(schema.get("oneOf", schema.get("anyOf"))[0])
    kind = schema.get("type")
    if isinstance(kind, list):
        return example({**schema, "type": kind[0]})
    if kind == "object":
        return {k: example(v) for k, v in schema.get("properties", {}).items() if k in schema.get("required", [])}
    if kind == "array":
        return [example(schema.get("items", {})) for _ in range(schema.get("minItems", 0))]
    return {"string": "example", "integer": 1, "number": 1.5, "boolean": True, "null": None}.get(kind, "example")


def format_calls(calls, family="qwen"):
    if not calls:
        return "NO_CALL"
    if family == "qwen":
        return "\n".join("<tool_call>\n" + json.dumps(x, ensure_ascii=False) + "\n</tool_call>" for x in calls)
    return json.dumps(calls[0] if len(calls) == 1 else calls, ensure_ascii=False)
