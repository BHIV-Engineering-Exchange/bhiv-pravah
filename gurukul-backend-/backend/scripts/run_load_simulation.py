from app.services.prana_load_tester import prana_load_tester
import json

def run_simulation():
    print("--- Starting Load Test Simulation (TANTRA Closure) ---")
    results = prana_load_tester.run_load_test(
        events_count=100, # Using 100 for a quick but meaningful test in this env
        concurrency=10,
        replay_workers=2
    )
    print(json.dumps(results, indent=2))
    print("--- Load Test Simulation Complete ---")

if __name__ == "__main__":
    run_simulation()
