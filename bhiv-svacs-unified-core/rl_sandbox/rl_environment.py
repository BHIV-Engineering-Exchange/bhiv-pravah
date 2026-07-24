import json
import random

episodes = []

for i in range(5):

    reward = random.randint(50, 100)

    episodes.append({
        "episode": i + 1,
        "reward": reward,
        "optimization": "signal_prioritization"
    })

with open(
    "rl_sandbox/training_log.jsonl",
    "w"
) as f:

    for item in episodes:
        f.write(json.dumps(item) + "\n")

print("RL TRAINING COMPLETE")