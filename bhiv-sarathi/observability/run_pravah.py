import os
import sys

# Ensure the observability package is on the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from pravah_adapter import start_heartbeat

if __name__ == "__main__":
    # Emit a heartbeat every 60 seconds (default)
    start_heartbeat(interval_seconds=60)
    # Keep the script alive – the heartbeat runs in a daemon thread.
    # Prevent the process from exiting immediately.
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass
