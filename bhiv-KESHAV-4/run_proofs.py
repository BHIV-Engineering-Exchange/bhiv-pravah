import json
import logging
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

from tantra.pipeline import run_tantra_pipeline
from tantra import bucket, insightflow

import io
log_stream = io.StringIO()
logging.basicConfig(level=logging.INFO, stream=log_stream, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("proofs")

def reset_state():
    bucket.clear()
    insightflow.clear()
    log_stream.truncate(0)
    log_stream.seek(0)

scenarios = []

def run_scenario(name, inputs, run_fn):
    reset_state()
    res = run_fn(inputs)
    logs = log_stream.getvalue()
    b_res = bucket.all_trace_ids()
    i_res = insightflow.get_events()
    
    scenarios.append({
        "name": name,
        "inputs": inputs,
        "output": res,
        "bucket": [bucket.read(tid) for tid in b_res],
        "insightflow": i_res,
        "logs": logs
    })

# Scenario 1: Normal Execution (no blockages)
input_1 = {
    "trace_id": "trace-normal-01",
    "execution_id": "exec-normal-01",
    "tasks": [{"task_id": "T1", "depends_on": []}],
    "constraint_results": [{"task_id": "T1", "is_valid": True, "unsatisfied_dependencies": []}],
    "propagation_results": [{"task_id": "T1", "affected_tasks": [], "impact_score": 0}]
}
run_scenario("Scenario 1: Normal execution", input_1, lambda i: run_tantra_pipeline(i))

# Scenario 2: Dependency Blockage
input_2 = {
    "trace_id": "trace-block-01",
    "execution_id": "exec-block-01",
    "tasks": [
        {"task_id": "T1", "depends_on": []},
        {"task_id": "T2", "depends_on": ["T1"]}
    ],
    "constraint_results": [
        {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []},
        {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]}
    ],
    "propagation_results": [
        {"task_id": "T1", "affected_tasks": ["T2"], "impact_score": 10},
        {"task_id": "T2", "affected_tasks": [], "impact_score": 4}
    ]
}
run_scenario("Scenario 2: Dependency blockage", input_2, lambda i: run_tantra_pipeline(i))

# Scenario 3: Corrupted Input
input_3 = {
    "execution_id": "exec-corrupt-01",
    # trace_id intentionally missing
    "tasks": [{"task_id": "T1", "depends_on": []}]
}
run_scenario("Scenario 3: Corrupted input", input_3, lambda i: run_tantra_pipeline(i))

# Scenario 4: Parallel Traces
def run_parallel(inputs):
    def run_one(trace_suffix):
        i = deepcopy(inputs)
        i["trace_id"] = f"trace-parallel-0{trace_suffix}"
        return run_tantra_pipeline(i)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_one, i) for i in range(1, 6)]
        return [f.result() for f in futures]

input_4 = {
    "execution_id": "exec-parallel-01",
    "tasks": [{"task_id": "T1", "depends_on": []}],
    "constraint_results": [{"task_id": "T1", "is_valid": True, "unsatisfied_dependencies": []}],
    "propagation_results": [{"task_id": "T1", "affected_tasks": [], "impact_score": 0}]
}
run_scenario("Scenario 4: Parallel traces", input_4, run_parallel)

# Scenario 5: Replay Execution
def run_replay(inputs):
    res1 = run_tantra_pipeline(inputs)
    res2 = run_tantra_pipeline(inputs)
    return {"run_1": res1, "run_2_replay": res2}

input_5 = deepcopy(input_2)
input_5["trace_id"] = "trace-replay-01"
run_scenario("Scenario 5: Replay execution", input_5, run_replay)

# Generate Markdown
md = ["# KESHAV End-to-End Proof\n**Phase 4 — End-to-End Execution Proof**\n\n"]

for s in scenarios:
    md.append(f"## {s['name']}")
    md.append("### Input")
    md.append(f"```json\n{json.dumps(s['inputs'], indent=2)}\n```")
    md.append("### Output")
    md.append(f"```json\n{json.dumps(s['output'], indent=2, default=str)}\n```")
    md.append("### Bucket Result")
    md.append(f"```json\n{json.dumps(s['bucket'], indent=2, default=str)}\n```")
    md.append("### InsightFlow Result")
    md.append(f"```json\n{json.dumps(s['insightflow'], indent=2, default=str)}\n```")
    md.append("### Logs")
    md.append(f"```text\n{s['logs'].strip()}\n```\n")
    md.append("---\n")

with open(r"c:\rajaryan\KESHAV-4\END_TO_END_PROOF.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print("END_TO_END_PROOF.md created successfully.")
