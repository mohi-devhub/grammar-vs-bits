from qunti.grammar import format_calls
from qunti.scoring import score


def item(category="simple", expected=None):
    return {"id": "unit", "category": category, "source_category": "simple_python" if category == "simple" else category,
            "input": {"function": [{"name": "math.square", "parameters": {
                "type": "dict", "properties": {"x": {"type": "integer"}}, "required": ["x"]}}]},
            "expected": expected or [{"math.square": {"x": [7]}}]}


def test_official_checker_accepts_reference_and_rejects_wrong_value():
    assert score(item(), format_calls([{"name": "math.square", "arguments": {"x": 7}}]))["correct"]
    wrong = score(item(), format_calls([{"name": "math.square", "arguments": {"x": 8}}]))
    assert not wrong["correct"] and wrong["schema_valid"]


def test_parallel_is_unordered_but_multiplicity_is_preserved():
    case = item("parallel", [{"math.square": {"x": [7]}}, {"math.square": {"x": [8]}}])
    calls = [{"name": "math.square", "arguments": {"x": 8}}, {"name": "math.square", "arguments": {"x": 7}}]
    assert score(case, format_calls(calls))["correct"]
    assert not score(case, format_calls(calls[:1]))["correct"]


def test_duplicate_json_keys_are_not_silently_overwritten():
    result = score(item(), '<tool_call>{"name":"math.square","arguments":{"x":8,"x":7}}</tool_call>')
    assert not result["correct"] and result["invalid_json_or_format"]


def test_truncation_is_failure_even_when_prefix_is_parseable():
    assert not score(item(), format_calls([{"name": "math.square", "arguments": {"x": 7}}]), completed=False)["correct"]


def test_official_irrelevance_and_format_are_separate():
    result = score(item("irrelevance"), "I cannot call a suitable tool.")
    assert result["correct"] and result["invalid_json_or_format"]
    assert not score(item("irrelevance"), format_calls([{"name": "math.square", "arguments": {"x": 7}}]))["correct"]


def test_malformed_call_name_cannot_crash_taxonomy():
    from qunti.diagnostics import taxonomy
    text = '<tool_call>{"name":{},"arguments":{}}</tool_call>'
    result = score(item(), text)
    assert taxonomy(item(), text, result)["primary"] == "invalid_json_or_format"
