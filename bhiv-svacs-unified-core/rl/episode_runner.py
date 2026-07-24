import json
from rl.reward_model import calculate_reward


def run_episode():

    reward = calculate_reward(45)

    episode = {
        "episode_id": "EP-001",
        "reward": reward,
        "status": "COMPLETED"
    }

    with open("rl/learning_episode_log.json", "w") as f:
        json.dump(episode, f, indent=2)

    return episode