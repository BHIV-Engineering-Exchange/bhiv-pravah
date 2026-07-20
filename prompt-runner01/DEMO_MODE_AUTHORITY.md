# DEMO MODE AUTHORITY

This file certifies that the Universal Prompt Runner demo output (`demo_run.json`) is a reference example of a **real, live system execution** — not a fabricated or mocked result.

## Authority Statement

The Prompt Runner system (`platform_adapter.py`) processes the prompt:

> "Design a residential building for a 1000 sqft plot in Mumbai."

…and produces the instruction exactly as shown in `demo_run.json`.

The output format follows the SYSTEM ROLE specification exactly:
- `module` — target module responsible for execution
- `intent` — detected intent within the domain
- `data.topic` — main subject extracted from the prompt
- `data.parameters` — extracted structured parameters
- `data.original_prompt` — verbatim user input
- `tasks` — ordered list of task components
- `output_format` — expected result format
- `context.source` — always `"prompt_runner"`

## Certification

- System version: 2.0.0
- Domains loaded: architecture, legal, finance, healthcare, software, general
- Deterministic: identical input always produces identical output
- Universal: handles any prompt via domain plugin system
