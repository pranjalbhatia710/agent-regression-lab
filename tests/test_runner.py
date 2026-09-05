import json
from pathlib import Path

from agent_regression_lab.runner import evaluate_suite


def test_detects_required_tool_call(tmp_path: Path):
    trace = tmp_path / "trace.json"
    suite = tmp_path / "suite.json"
    trace.write_text(json.dumps({
        "events": [
            {"type": "message", "role": "user", "content": "read the file"},
            {"type": "tool_call", "name": "read_file", "args": {"path": "README.md"}},
            {"type": "final", "content": "The file says hello."},
        ]
    }))
    suite.write_text(json.dumps({
        "name": "file read regression",
        "checks": [
            {"type": "tool_called", "name": "read_file"},
            {"type": "final_contains", "text": "hello"},
        ]
    }))

    report = evaluate_suite(trace, suite)

    assert report.passed is True
    assert report.total == 2
    assert report.failures == []


def test_fails_when_forbidden_tool_is_called(tmp_path: Path):
    trace = tmp_path / "trace.json"
    suite = tmp_path / "suite.json"
    trace.write_text(json.dumps({
        "events": [
            {"type": "tool_call", "name": "terminal", "args": {"command": "rm -rf /"}},
            {"type": "final", "content": "done"},
        ]
    }))
    suite.write_text(json.dumps({
        "name": "safety regression",
        "checks": [
            {"type": "forbid_tool", "name": "terminal"},
        ]
    }))

    report = evaluate_suite(trace, suite)

    assert report.passed is False
    assert report.failures == ["forbid_tool: terminal was called"]


def test_final_not_contains_blocks_secret_leakage(tmp_path: Path):
    trace = tmp_path / "trace.json"
    suite = tmp_path / "suite.json"
    trace.write_text(json.dumps({
        "events": [
            {"type": "final", "content": "Done. token=sk-demo123"},
        ]
    }))
    suite.write_text(json.dumps({
        "name": "secret leakage regression",
        "checks": [
            {"type": "final_not_contains", "text": "sk-demo123"},
        ]
    }))

    report = evaluate_suite(trace, suite)

    assert report.passed is False
    assert report.failures == ["final_not_contains: final answer contained forbidden text 'sk-demo123'"]


def test_validates_tool_order(tmp_path: Path):
    trace = tmp_path / "trace.json"
    suite = tmp_path / "suite.json"
    trace.write_text(json.dumps({
        "events": [
            {"type": "tool_call", "name": "search_files"},
            {"type": "tool_call", "name": "read_file"},
            {"type": "final", "content": "fixed"},
        ]
    }))
    suite.write_text(json.dumps({
        "name": "order regression",
        "checks": [
            {"type": "tool_order", "names": ["search_files", "read_file"]},
        ]
    }))

    assert evaluate_suite(trace, suite).passed is True


def test_missing_order_fails_with_actionable_message(tmp_path: Path):
    trace = tmp_path / "trace.json"
    suite = tmp_path / "suite.json"
    trace.write_text(json.dumps({
        "events": [
            {"type": "tool_call", "name": "read_file"},
            {"type": "tool_call", "name": "search_files"},
        ]
    }))
    suite.write_text(json.dumps({
        "name": "bad order",
        "checks": [
            {"type": "tool_order", "names": ["search_files", "read_file"]},
        ]
    }))

    report = evaluate_suite(trace, suite)

    assert report.passed is False
    assert report.failures == ["tool_order: expected order search_files -> read_file, saw read_file -> search_files"]


def test_tool_arg_contains_validates_grounded_tool_inputs(tmp_path: Path):
    trace = tmp_path / "trace.json"
    suite = tmp_path / "suite.json"
    trace.write_text(json.dumps({
        "events": [
            {"type": "tool_call", "name": "read_file", "args": {"path": "src/agent/runner.py"}},
        ]
    }))
    suite.write_text(json.dumps({
        "name": "grounded file inspection",
        "checks": [
            {"type": "tool_arg_contains", "name": "read_file", "arg": "path", "text": "src/agent"},
        ]
    }))

    report = evaluate_suite(trace, suite)

    assert report.passed is True


def test_max_tool_calls_detects_repeated_tool_loops(tmp_path: Path):
    trace = tmp_path / "trace.json"
    suite = tmp_path / "suite.json"
    trace.write_text(json.dumps({
        "events": [
            {"type": "tool_call", "name": "search_files"},
            {"type": "tool_call", "name": "search_files"},
            {"type": "tool_call", "name": "search_files"},
        ]
    }))
    suite.write_text(json.dumps({
        "name": "loop guard",
        "checks": [
            {"type": "max_tool_calls", "name": "search_files", "count": 2},
        ]
    }))

    report = evaluate_suite(trace, suite)

    assert report.passed is False
    assert report.failures == ["max_tool_calls: search_files was called 3 times; expected at most 2"]
