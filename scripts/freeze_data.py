import json
import random
from collections import Counter
from pathlib import Path
from qunti.common import ROOT, digest, read_jsonl, write_json
from qunti.grammar import build


def main():
    protocol = json.loads((ROOT / "configs/protocol.json").read_text())
    source = json.loads((ROOT / "docs/BFCL_SOURCE.json").read_text())
    data = ROOT / "vendor/bfcl/bfcl_eval/data"
    output, inputs = [], {}
    kinds, keywords = Counter(), Counter()
    for category, count in protocol["category_counts"].items():
        upstream = "simple_python" if category == "simple" else category
        path = data / f"BFCL_v4_{upstream}.json"
        inputs[str(path.relative_to(ROOT))] = digest(path.read_bytes())
        answers_path = data / "possible_answer" / path.name
        answers = {}
        if answers_path.exists():
            inputs[str(answers_path.relative_to(ROOT))] = digest(answers_path.read_bytes())
            answers = {v["id"]: v for v in read_jsonl(answers_path)}
        pool = sorted(read_jsonl(path), key=lambda x: x["id"])
        rng = random.Random(f'{protocol["dataset_seed"]}:{category}')
        chosen = rng.sample(pool, count)
        for raw in chosen:
            expected = answers.get(raw["id"], {}).get("ground_truth", [])
            item = {"id": raw["id"], "category": category, "source_category": upstream,
                    "input": raw, "expected": expected, "input_sha256": digest(raw)}
            output.append(item)
            for family in ("qwen", "llama"):
                for arm in ("loose", "trigger_strict", "whole_strict"):
                    grammar = build(raw["function"], family, arm)
                    target = ROOT / "data/grammars" / family / arm / (raw["id"] + ".gbnf")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(grammar)
    output.sort(key=lambda x: (x["category"], x["id"]))
    path = ROOT / "data/frozen.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in output))
    pilot_ids = []
    for category, count in {"simple": 15, "multiple": 15, "parallel": 15, "irrelevance": 5}.items():
        candidates = [x["id"] for x in output if x["category"] == category]
        random.Random(f'pilot:{protocol["dataset_seed"]}:{category}').shuffle(candidates)
        pilot_ids.extend(candidates[:count])
    write_json(ROOT / "data/pilot_ids.json", pilot_ids)
    write_json(ROOT / "data/manifest.json", {
        "bfcl_source": source, "selection_seed": protocol["dataset_seed"],
        "selection": "sort IDs, Random(str(seed)+':'+category).sample; no success-based filtering",
        "counts": dict(Counter(x["category"] for x in output)), "items": len(output),
        "frozen_sha256": digest(path.read_bytes()), "upstream_file_sha256": inputs,
        "pilot_items": len(pilot_ids), "pilot_ids_sha256": digest(pilot_ids),
        "references_visible_to_grammar_builder": False,
    })
    print(f"Frozen {len(output)} items; pilot {len(pilot_ids)} items; all requested schemas compiled.")


if __name__ == "__main__":
    main()
