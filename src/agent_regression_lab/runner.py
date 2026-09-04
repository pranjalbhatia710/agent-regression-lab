from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Report:
    suite: str
    passed: bool
    total: int
    failures: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "passed": self.passed,
            "total": self.total,
            "failures": self.failures,
        }


def evaluate_suite(trace_path: str | Path, suite_path: str | Path) -> Report:
    trace = _read_json(Path(trace_path))
    suite = _read_json(Path(suite_path))
    events = trace.get("events", [])
    checks = suite.get("checks", [])

    failures: list[str] = []
    for check in checks:
        failure = _evaluate_check(check, events)
        if failure:
            failures.append(failure)

    return Report(
        suite=suite.get("name", str(suite_path)),
        passed=not failures,
        total=len(checks),
        failures=failures,
    )


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _evaluate_check(check: dict[str, Any], events: list[dict[str, Any]]) -> str | None:
    check_type = check.get("type")
    if check_type == "tool_called":
        return _check_tool_called(str(check["name"]), events)
    if check_type == "forbid_tool":
        return _check_forbid_tool(str(check["name"]), events)
    if check_type == "final_contains":
        return _check_final_contains(str(check["text"]), events)
    if check_type == "final_not_contains":
        return _check_final_not_contains(str(check["text"]), events)
    if check_type == "tool_order":
        return _check_tool_order([str(name) for name in check["names"]], events)
    return f"unknown_check: {check_type}"


def _tool_names(events: list[dict[str, Any]]) -> list[str]:
    return [str(event.get("name")) for event in events if event.get("type") == "tool_call"]


def _check_tool_called(name: str, events: list[dict[str, Any]]) -> str | None:
    if name in _tool_names(events):
        return None
    return f"tool_called: {name} was not called"


def _check_forbid_tool(name: str, events: list[dict[str, Any]]) -> str | None:
    if name in _tool_names(events):
        return f"forbid_tool: {name} was called"
    return None


def _check_final_contains(text: str, events: list[dict[str, Any]]) -> str | None:
    finals = [str(event.get("content", "")) for event in events if event.get("type") == "final"]
    if any(text in final for final in finals):
        return None
    return f"final_contains: final answer did not contain {text!r}"


def _check_final_not_contains(text: str, events: list[dict[str, Any]]) -> str | None:
    finals = [str(event.get("content", "")) for event in events if event.get("type") == "final"]
    if any(text in final for final in finals):
        return f"final_not_contains: final answer contained forbidden text {text!r}"
    return None


def _check_tool_order(names: list[str], events: list[dict[str, Any]]) -> str | None:
    seen = _tool_names(events)
    position = 0
    for tool in seen:
        if position < len(names) and tool == names[position]:
            position += 1
    if position == len(names):
        return None
    return f"tool_order: expected order {' -> '.join(names)}, saw {' -> '.join(seen)}"
