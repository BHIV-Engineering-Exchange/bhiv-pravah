import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env.integration_bridge"
EXAMPLE_FILE = ROOT / ".env.integration_bridge.example"
SCRIPT_FILE = ROOT / "integration_bridge_v2.py"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    print(f"Loading environment variables from: {path.name}")
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


if __name__ == "__main__":
    if not SCRIPT_FILE.exists():
        print("ERROR: integration_bridge_v2.py not found in repository root.")
        sys.exit(1)

    if not ENV_FILE.exists():
        if EXAMPLE_FILE.exists():
            print("WARNING: .env.integration_bridge not found.")
            print(f"Copy {EXAMPLE_FILE.name} to {ENV_FILE.name} and edit it for your deployment.")
        else:
            print("ERROR: No .env.integration_bridge or example env file found.")
        sys.exit(1)

    load_env_file(ENV_FILE)

    print("Starting Integration Bridge using integration_bridge_v2.py...")
    subprocess.run([sys.executable, str(SCRIPT_FILE)], check=True)
