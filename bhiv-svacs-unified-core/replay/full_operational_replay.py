import json
import os

execution_id = "exec_c5a61f26"

replay_file = f"storage/replay/{execution_id}.json"

if not os.path.exists(replay_file):

    print("Replay file not found")

else:

    with open(
        replay_file,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    output_path = (
        "storage/replay/operational_replay_proof.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as outfile:

        json.dump(
            data,
            outfile,
            indent=4
        )

    print(
        json.dumps(
            data,
            indent=4
        )
    )
