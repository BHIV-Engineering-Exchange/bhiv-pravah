# Intelligence Integration Documentation

## Overview

This module implements the Autonomous Intelligence Layer.

The purpose of this layer is to generate the next task automatically
based on the review output from the scoring engine.

This replaces the manual task assignment process.


## Runtime Flow

Submission
→ Review Output
→ Intelligence Engine
→ Next Task Generation
→ Product Response


## Main Component

TaskIntelligenceEngine

Method:
generate_next_task(review_output)

Input:
review_output from scoring engine

Output:
next_task object


## Decision Rules

score < 40 → correction task

40 ≤ score < 70 → reinforcement task

score ≥ 70 → advance task


## Architecture Guard

Ensures next task follows:

- same track
- correct progression
- no random assignment


## Output Contract

next_task:

- title
- objective
- focus_area
- difficulty
- expected_deliverables


## Determinism

Same review output always produces the same next task.


## Files

engine/
adapter/
models/
registry/
runtime_simulation.py


## Status

Intelligence layer integrated successfully.
Ready for orchestrator connection.