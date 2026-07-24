# KESHAV Dependency Intelligence API: How It Works

## 1. What does the project do?
This API is designed to analyze **failed or blocked execution pipelines**. If you have a system running multiple dependent tasks (e.g., Task B needs Task A to finish first), and something goes wrong, you send the data to this API. 

The API analyzes the graph of dependencies, figures out exactly **which task is the root cause of the failure**, calculates how badly that failure impacts everything else, and recommends an action to fix it.

---

## 2. What input should it take?
The API expects a `POST` request to `http://localhost:5000/analyze` with a JSON body. The input describes the state of your tasks and what went wrong.

Here is a full valid sample input:

```json
{
  "trace_id": "upstream-trace-001",
  "execution_id": "exec-001",
  "tasks": [
    { "task_id": "Task_A", "depends_on": [] },
    { "task_id": "Task_B", "depends_on": ["Task_A"] }
  ],
  "constraint_results": [
    { "task_id": "Task_A", "is_valid": false, "unsatisfied_dependencies": [] },
    { "task_id": "Task_B", "is_valid": false, "unsatisfied_dependencies": ["Task_A"] }
  ],
  "propagation_results": [
    { "task_id": "Task_A", "affected_tasks": ["Task_B"], "impact_score": 10 },
    { "task_id": "Task_B", "affected_tasks": [], "impact_score": 4  }
  ]
}
```

### Explanation of the input fields:
* **`trace_id`** / **`execution_id`**: Unique identifiers for tracking this specific run.
* **`tasks`**: A list of all tasks involved in this run and what they depend on. (In the example, `Task_B` depends on `Task_A`).
* **`constraint_results`**: A list that tells the API which tasks failed (`is_valid: false`) and *why* (e.g., `Task_B` failed because it had unsatisfied dependencies on `Task_A`).
* **`propagation_results`**: Information indicating how many downstream tasks are affected if a specific task fails, along with a numerical score of the impact.

---

## 3. How do you get the output?
You get the output directly as a JSON response in the same `POST` request. 

Based on the sample input above, the API does the following behind the scenes:
1. It sees that `Task_B` failed, but traces the failure back to `Task_A` (the **root cause**).
2. It sees that `Task_A` has a high impact score of 10.
3. It figures out that `Task_A` needs to be unblocked for the system to recover.

### The output response will look like this:
```json
{
  "trace_id": "upstream-trace-001",
  "execution_id": "exec-001",
  "root_cause": "Task_A",
  "resolution_signal": "UNBLOCK_DEPENDENCY:Task_A",
  "impact_score": 10,
  "severity": "HIGH",
  "timestamp": "2026-07-07T14:45:00Z"
}
```

### What the output means:
* **`root_cause`**: The API successfully figured out that `Task_A` was the culprit.
* **`resolution_signal`**: A specific, machine-readable action recommendation to fix the issue (`UNBLOCK_DEPENDENCY:Task_A`).
* **`severity`**: Categorizes the failure (e.g., `HIGH` severity because of the high impact score).

---

## 4. How to Test
1. Open [http://localhost:5000/apidocs/](http://localhost:5000/apidocs/) in your browser.
2. Click on the `POST /analyze` endpoint and click **Try it out**.
3. Paste the sample JSON input into the request body and hit **Execute**.
4. You'll see the exact output returned at the bottom.
