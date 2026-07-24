import json
import os
from typing import Set

STORE_FILE = "replay_store.json"

def _load() -> Set[str]:
    if not os.path.exists(STORE_FILE):
        return set()
    with open(STORE_FILE, "r") as f:
        return set(json.load(f))

def _save(seen: Set[str]) -> None:
    with open(STORE_FILE, "w") as f:
        json.dump(list(seen), f)

def check_and_store(nonce: str) -> bool:
    seen = _load()

    # Replay detected
    if nonce in seen:
        return False

    # First time seen
    seen.add(nonce)
    _save(seen)
    return True
