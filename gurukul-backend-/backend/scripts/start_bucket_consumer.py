"""
Start the Bucket Consumer service (integrated mode)

Since Karma Tracker is now integrated into the backend,
the consumer uses the same backend URL for both bucket and karma endpoints.
"""

import subprocess
import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Start the Karma Tracker Bucket Consumer (integrated mode).")
    parser.add_argument("--backend-url", default="http://localhost:3000",
                        help="Base URL for the Gurukul Backend (includes both bucket and karma endpoints).")
    parser.add_argument("--poll-interval", type=int, default=5,
                        help="Polling interval in seconds.")
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Number of packets to fetch and process in each batch.")
    args = parser.parse_args()

    # Set environment variables for the consumer
    os.environ["BUCKET_API_BASE_URL"] = args.backend_url
    # In integrated mode, karma tracker uses the same URL
    os.environ["KARMA_TRACKER_API_BASE_URL"] = args.backend_url
    os.environ["POLL_INTERVAL_SECONDS"] = str(args.poll_interval)
    os.environ["BATCH_SIZE"] = str(args.batch_size)

    # Path to the bucket_consumer.py script
    consumer_script_path = os.path.join(os.path.dirname(__file__), "..", "app", "utils", "karma", "bucket_consumer.py")

    print(f"Starting Bucket Consumer (Integrated Mode) with settings:")
    print(f"  Backend URL: {args.backend_url} (bucket + karma endpoints)")
    print(f"  Poll Interval: {args.poll_interval} seconds")
    print(f"  Batch Size: {args.batch_size} packets")
    print(f"  Consumer Script: {consumer_script_path}")
    print("-" * 50)

    try:
        # Use sys.executable to ensure the correct Python interpreter from the venv is used
        subprocess.run([sys.executable, consumer_script_path])
    except FileNotFoundError:
        print(f"Error: Python interpreter not found. Ensure Python is installed and in PATH, or activate your virtual environment.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

