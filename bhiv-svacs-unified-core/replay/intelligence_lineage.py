import json
import os

TELEMETRY_FILE = "storage/telemetry/telemetry_logs.json"
OUTPUT_FILE = "storage/lineage/lineage_report.json"

execution_id = "exec_b29df690"


def load_json_lines(path):

    records = []

    if not os.path.exists(path):
        return records

    with open(path, "r", encoding="utf-8") as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))

            except:
                pass

    return records


events = load_json_lines(TELEMETRY_FILE)

lineage = []

trace_id = "UNKNOWN"

for event in events:

    if event.get("execution_id") == execution_id:

        trace_id = event.get("trace_id")

        lineage.append({

            "stage": event.get("stage"),

            "service": event.get("service"),

            "status": event.get("status"),

            "timestamp": event.get("timestamp")
        })

report = {

    "execution_id": execution_id,

    "trace_id": trace_id,

    "lineage": lineage
}

os.makedirs(
    "storage/lineage",
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        report,
        file,
        indent=4
    )

print(
    json.dumps(
        report,
        indent=4
    )
)
