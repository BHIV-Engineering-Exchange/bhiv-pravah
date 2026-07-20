import asyncio
import httpx
import time
import sys

# Standardized Ports
CORE_URL = "http://127.0.0.1:3001/api/v1"
EMS_URL = "http://127.0.0.1:3002/api/v1"

async def single_request(client, worker_id, target_url):
    start = time.time()
    try:
        response = await client.get(f"{target_url}/health")
        duration = time.time() - start
        return {"worker_id": worker_id, "status": response.status_code, "duration": duration, "target": target_url}
    except Exception as e:
        return {"worker_id": worker_id, "status": "error", "error": str(e), "target": target_url}

async def main(concurrency=50):
    print(f"[Global Stress] Starting 1:1 concurrency test on {concurrency} workers...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Split load between Core and EMS
        tasks = []
        for i in range(concurrency):
            url = CORE_URL if i % 2 == 0 else EMS_URL
            tasks.append(single_request(client, i, url))
        
        results = await asyncio.gather(*tasks)
    
    # Analysis
    core_results = [r for r in results if r["target"] == CORE_URL]
    ems_results = [r for r in results if r["target"] == EMS_URL]
    
    def analyze(subset, name):
        successful = [r for r in subset if r.get("status") == 200]
        durations = [r["duration"] for r in successful]
        if durations:
            avg = sum(durations) / len(durations)
            print(f"[Stress] {name} | Success: {len(successful)}/{len(subset)} | Avg: {avg:.4f}s")
        else:
            print(f"[Stress] {name} | ALL REQUESTS FAILED")

    analyze(core_results, "Core Backend")
    analyze(ems_results, "EMS Backend")

if __name__ == "__main__":
    concurrency = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    asyncio.run(main(concurrency))
