"""Observable deterministic flags; official BFCL remains correctness authority."""
from collections import Counter
from qunti.grammar import normalize
from qunti.scoring import parse_calls
from jsonschema import Draft202012Validator


def taxonomy(item, text, scored, family="qwen"):
    flags = {k: False for k in ("invalid_json_or_format", "wrong_function", "missing_args", "extra_args",
                               "wrong_arg_type", "wrong_arg_value", "hallucinated_function", "hallucinated_args",
                               "missing_calls", "extra_calls")}
    flags["invalid_json_or_format"] = scored["invalid_json_or_format"]
    try:
        calls = parse_calls(text, family)
    except (ValueError, TypeError):
        return {"flags": flags, "primary": "invalid_json_or_format"}
    offered = {t["name"]: t for t in item["input"]["function"]}
    gold_names = Counter(next(iter(x)) for x in item["expected"])
    selected = Counter(c.get("name") for c in calls)
    all_keys = set().union(*(t["parameters"].get("properties", {}).keys() for t in offered.values()))
    flags["missing_calls"] = sum(selected.values()) < sum(gold_names.values())
    flags["extra_calls"] = sum(selected.values()) > sum(gold_names.values())
    key = "arguments" if family == "qwen" else "parameters"
    for call in calls:
        name = call.get("name")
        if name not in offered:
            flags["hallucinated_function"] = True
            continue
        if not scored["correct"] and name not in gold_names:
            flags["wrong_function"] = True
        args = call.get(key)
        if not isinstance(args, dict):
            flags["wrong_arg_type"] = True
            continue
        schema = normalize(offered[name]["parameters"])
        allowed = schema.get("properties", {})
        flags["missing_args"] |= bool(set(schema.get("required", [])) - args.keys())
        extra = set(args) - allowed.keys()
        flags["extra_args"] |= bool(extra)
        flags["hallucinated_args"] |= bool(extra - all_keys)
        errors = list(Draft202012Validator(schema).iter_errors(args))
        flags["wrong_arg_type"] |= any(e.validator == "type" for e in errors)
        flags["wrong_arg_value"] |= any(e.validator == "enum" for e in errors)
    official = scored.get("official") or {}
    kind = official.get("error_type", "")
    if not scored["correct"]:
        flags["wrong_arg_type"] |= "type_error" in kind
        flags["missing_args"] |= "missing_required" in kind or "missing_optional" in kind
        flags["extra_args"] |= "unexpected_param" in kind
        flags["wrong_arg_value"] |= "value_error" in kind and not flags["wrong_arg_type"]
    # Do not label a schema-valid parallel matching ambiguity as a known value
    # error without evidence from the official checker. Keep its raw error.
    order = ("invalid_json_or_format", "hallucinated_function", "wrong_function", "hallucinated_args",
             "extra_args", "missing_args", "wrong_arg_type", "wrong_arg_value", "missing_calls", "extra_calls")
    primary = next((k for k in order if flags[k]), "none" if scored["correct"] else "unresolved_official_failure")
    return {"flags": flags, "primary": primary, "official_error_type": kind}
