"""Run real llama.cpp grammar membership checks without loading model weights."""
import argparse
import json
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from qunti.common import ROOT, digest, now, read_jsonl, write_json
from qunti.grammar import call_schema, example, format_calls
import jsonschema


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validator", default=str(ROOT / ".cache/llama-build/bin/test-gbnf-validator"))
    args = parser.parse_args()
    cases = []
    for item in read_jsonl(ROOT / "data/frozen.jsonl"):
        tools = item["input"]["function"]
        for family in ("qwen", "llama"):
            arg = "arguments" if family == "qwen" else "parameters"
            calls = []
            for tool in tools:
                call = {"name": tool["name"], arg: example(tool["parameters"])}
                jsonschema.validate(call, call_schema(tools, family))
                calls.append(call)
                cases.append((item["id"], family, "whole_strict", "schema_witness:" + tool["name"], format_calls([call], family), True))
            good = calls[0]
            reordered = {arg: dict(reversed(list(good[arg].items()))), "name": good["name"]}
            for label, text, valid in [
                ("reordered_object_keys", format_calls([reordered], family), True),
                ("parallel_without_gold_count", format_calls([good, good], family), True),
                ("explicit_no_call", "NO_CALL", True),
                ("malformed", '{"name":', False),
                ("free_text", "I will call a tool soon.", False),
                ("whitespace_only", "  \n ", False),
                ("unknown_function", format_calls([{**good, "name": "__not_offered__"}], family), False),
                ("extra_arg", format_calls([{**good, arg: {**good[arg], "__not_documented__": 1}}], family), False),
            ]:
                cases.append((item["id"], family, "whole_strict", label, text, valid))
            required = tools[0]["parameters"].get("required", [])
            if required:
                missing = {k: v for k, v in good[arg].items() if k != required[0]}
                cases.append((item["id"], family, "whole_strict", "missing_required", format_calls([{**good, arg: missing}], family), False))
                field_schema = tools[0]["parameters"].get("properties", {}).get(required[0], {})
                if field_schema.get("type") != "null":
                    bad = {**good[arg], required[0]: None}
                    cases.append((item["id"], family, "whole_strict", "wrong_type", format_calls([{**good, arg: bad}], family), False))
            for label, text in [("loose_admits_malformed", '{"name":'), ("loose_admits_prose", "unrestricted"), ("loose_admits_whitespace", " \n ")]:
                cases.append((item["id"], family, "loose", label, text, True))
            cases.append((item["id"], family, "trigger_strict", "trigger_body_accepts_call", format_calls([good], family), True))
    def check(case):
        item_id, family, arm, label, text, expected = case
        grammar = ROOT / "data/grammars" / family / arm / (item_id + ".gbnf")
        with tempfile.NamedTemporaryFile("w", suffix=".txt") as f:
            f.write(text); f.flush()
            try:
                proc = subprocess.run([args.validator, str(grammar), f.name], capture_output=True, text=True, timeout=15)
                if proc.returncode or "Failed to initialize" in proc.stdout:
                    return {"id": item_id, "family": family, "arm": arm, "case": label, "passed": False,
                            "error": "validator_runtime", "details": (proc.stdout + proc.stderr)[-1500:]}
                # The upstream tool exits 0 for BOTH valid and invalid membership.
                actual = proc.stdout.startswith("Input string is valid according to the grammar.")
                return {"id": item_id, "family": family, "arm": arm, "case": label,
                        "expected_accept": expected, "actual_accept": actual, "passed": expected == actual}
            except subprocess.TimeoutExpired:
                return {"id": item_id, "family": family, "arm": arm, "case": label, "passed": False, "error": "timeout"}
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(check, cases))
    path = ROOT / "results/offline/grammar_membership.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in outcomes))
    failures = [r for r in outcomes if not r["passed"]]
    summary = {"date": now(), "llama_cpp_commit": "8542e94350f0ade01644db6f1d1520da3814dafd",
               "validator_sha256": digest(Path(args.validator).read_bytes()), "cases": len(outcomes),
               "passed": len(outcomes) - len(failures), "failed": len(failures), "examples_of_failure": failures[:5],
               "no_model_loaded": True, "gold_values_used_to_construct_tests": False,
               "scope": "Finite char-level membership checks, not a proof of token-level runtime coverage or semantic accuracy."}
    write_json(ROOT / "results/offline/grammar_validation.json", summary)
    print(json.dumps(summary, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
