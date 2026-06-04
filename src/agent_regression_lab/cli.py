from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_regression_lab.runner import evaluate_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arl",
        description="Run deterministic regression checks against an AI agent trace.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run a regression suite")
    run.add_argument("--trace", required=True, type=Path, help="path to trace JSON")
    run.add_argument("--suite", required=True, type=Path, help="path to suite JSON")
    run.add_argument("--json", action="store_true", help="print machine-readable report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        report = evaluate_suite(args.trace, args.suite)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            status = "PASS" if report.passed else "FAIL"
            print(f"{status} {report.suite}: {report.total} checks")
            for failure in report.failures:
                print(f"- {failure}")
        return 0 if report.passed else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
