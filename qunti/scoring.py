"""Use the pinned, unmodified official BFCL AST checker; never execute outputs."""
import ast
import importlib
import json
import re
import sys
import types
from functools import lru_cache
from qunti.common import ROOT
from qunti.grammar import call_schema
import jsonschema


def reject_constant(value):
    raise ValueError("Non-JSON number: " + value)


def unique_pairs(pairs):
    value = {}
    for k, v in pairs:
        if k in value:
            raise ValueError("Duplicate JSON key: " + k)
        value[k] = v
    return value


def parse_calls(text, family="qwen"):
    clean = text.strip()
    if clean == "NO_CALL":
        return []
    if family == "qwen":
        matches = list(re.finditer(r"<tool_call>\s*(.*?)\s*</tool_call>", clean, re.S))
        if not matches:
            raise ValueError("No complete native tool-call envelope")
        residue = re.sub(r"<tool_call>.*?</tool_call>", "", clean, flags=re.S).strip()
        if residue:
            raise ValueError("Extra content outside calls")
        parts = [m.group(1) for m in matches]
    else:
        parts = [clean]
    outputs = []
    for part in parts:
        obj = json.loads(part, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
        outputs.extend(obj if isinstance(obj, list) else [obj])
    if not outputs or any(not isinstance(x, dict) for x in outputs):
        raise ValueError("Expected nonempty call objects")
    arg_key = "arguments" if family == "qwen" else "parameters"
    if any(not isinstance(x.get("name"), str) or not isinstance(x.get(arg_key), dict) for x in outputs):
        raise ValueError("Malformed native call object: name/argument-object missing or wrong type")
    return outputs


@lru_cache(maxsize=1)
def official():
    sys.path.insert(0, str(ROOT / "vendor/bfcl"))
    # Upstream imports the provider registry to read this single normalization
    # flag. Avoid importing unrelated API clients; checker code is unchanged.
    registry = types.ModuleType("bfcl_eval.constants.model_config")
    registry.MODEL_CONFIG_MAPPING = {"grammar-vs-bits": types.SimpleNamespace(underscore_to_dot=False)}
    sys.modules[registry.__name__] = registry
    checker = importlib.import_module("bfcl_eval.eval_checker.ast_eval.ast_checker").ast_checker
    enums = importlib.import_module("bfcl_eval.constants.enums")
    return checker, enums.Language.PYTHON


@lru_cache(maxsize=1)
def official_irrelevance():
    # Extract the unchanged trusted upstream function to avoid importing every
    # provider SDK. Its handler only adapts our parsed call representation.
    path = ROOT / "vendor/bfcl/bfcl_eval/eval_checker/eval_runner.py"
    tree = ast.parse(path.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_evaluate_single_relevance_entry")
    node.returns = None
    for arg in node.args.args:
        arg.annotation = None
    namespace = {"ReturnFormat": types.SimpleNamespace(PYTHON="python"), "is_empty_output": lambda x: not x}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[node.name]


def score(item, text, family="qwen", completed=True):
    calls, parse_error = [], None
    try:
        calls = parse_calls(text, family)
    except (ValueError, TypeError) as exc:
        parse_error = str(exc)
    diagnostics = {"invalid_json_or_format": parse_error is not None, "schema_valid": False}
    if parse_error is None:
        try:
            for call in calls:
                jsonschema.validate(call, call_schema(item["input"]["function"], family))
            diagnostics["schema_valid"] = True
        except jsonschema.ValidationError:
            pass
    arg = "arguments" if family == "qwen" else "parameters"
    decoded = [{x.get("name"): x.get(arg)} for x in calls if isinstance(x.get("name"), str) and isinstance(x.get(arg), dict)]
    if item["category"] == "irrelevance":
        class Handler:
            def decode_ast(self, *args, **kwargs):
                if parse_error:
                    raise ValueError(parse_error)
                return decoded
        result = official_irrelevance()(Handler(), item["id"], text, item["input"], "grammar-vs-bits", "irrelevance")
        # Publish official irrelevance scoring AND our separate format/finish flags.
        return {"correct": bool(result["valid"]) and completed, "official": result, **diagnostics, "parse_error": parse_error}
    if parse_error or len(decoded) != len(calls) or not completed:
        return {"correct": False, "official": None, **diagnostics, "parse_error": parse_error, "completed": completed}
    checker, language = official()
    result = checker(item["input"]["function"], decoded, item["expected"], language, item["source_category"], "grammar-vs-bits")
    return {"correct": bool(result["valid"]), "official": result, **diagnostics, "parse_error": None, "completed": completed}
