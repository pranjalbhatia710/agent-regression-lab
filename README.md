# agent-regression-lab

Tiny regression tests for AI agent traces, tool calls, and final answers.

Most agent eval tools are either huge benchmark platforms or observability dashboards. `agent-regression-lab` is the small missing layer: a deterministic smoke-test harness you can run in CI every time you change an agent prompt, tool wrapper, model, or orchestration loop.

## What it checks

- required tool calls happened
- unsafe/forbidden tools were not called
- tool calls happened in the expected order
- repeated tool loops stayed under an explicit budget
- final answer contains required text

This is meant for boring reliability bugs:

- an agent stops searching before reading files
- a model update starts calling `terminal` when it should not
- final answers lose required fields
- tool order flips after a prompt change
- partial-failure recovery regresses

## Install locally

```bash
uv tool install git+https://github.com/pranjalbhatia710/agent-regression-lab.git
```

Or run from a checkout:

```bash
uv run arl run --trace examples/trace.pass.json --suite examples/suite.json
```

## Example

Trace:

```json
{
  "events": [
    {"type": "tool_call", "name": "search_files"},
    {"type": "tool_call", "name": "read_file"},
    {"type": "final", "content": "Found and fixed the config bug."}
  ]
}
```

Suite:

```json
{
  "name": "debugging agent smoke test",
  "checks": [
    {"type": "tool_called", "name": "search_files"},
    {"type": "tool_order", "names": ["search_files", "read_file"]},
    {"type": "forbid_tool", "name": "send_message"},
    {"type": "final_contains", "text": "fixed"}
  ]
}
```

Run:

```bash
arl run --trace examples/trace.pass.json --suite examples/suite.json
```

Output:

```text
PASS debugging agent smoke test: 4 checks
```

JSON output:

```bash
arl run --trace examples/trace.pass.json --suite examples/suite.json --json
```

## Check types

### `tool_called`

```json
{"type": "tool_called", "name": "read_file"}
```

Passes when a trace has a tool call with that name.

### `forbid_tool`

```json
{"type": "forbid_tool", "name": "terminal"}
```

Fails if the tool was called.

### `tool_order`

```json
{"type": "tool_order", "names": ["search_files", "read_file"]}
```

Passes when those tools appear in that order. Other tool calls may exist between them.

### `final_contains`

```json
{"type": "final_contains", "text": "fixed"}
```

Passes when any final event contains the text.

### `tool_arg_contains`

```json
{"type": "tool_arg_contains", "name": "read_file", "arg": "path", "text": "src/agent"}
```

Passes when at least one call to the named tool has an argument containing the
expected text. Use this to catch regressions where an agent still calls the right
tool but points it at the wrong file, URL, or command.

### `max_tool_calls`

```json
{"type": "max_tool_calls", "name": "search_files", "count": 2}
```

Passes when the named tool is called no more than `count` times. This is useful
for guarding against repeated search/read/retry loops that make agent runs slow,
expensive, or noisy without improving the final answer.

## Trace format

`agent-regression-lab` intentionally accepts a tiny JSON shape so it is easy to adapt from any agent framework:

```json
{
  "events": [
    {"type": "message", "role": "user", "content": "..."},
    {"type": "tool_call", "name": "read_file", "args": {"path": "README.md"}},
    {"type": "final", "content": "..."}
  ]
}
```

You can export this from LangGraph, CrewAI, OpenAI Responses traces, Hermes logs, Claude Code transcripts, or your own harness.

## Roadmap

- schema validation with line-level errors
- adapters for common agent trace formats
- JUnit output for CI
- snapshot tests for final answers
- latency/cost budget checks
- tool-argument assertions
- multiple suites per repo

## Why this can be useful

Agent products break in unsexy ways. The model still responds, but the workflow silently changes. This repo gives builders a cheap regression layer before they need a full eval platform.
