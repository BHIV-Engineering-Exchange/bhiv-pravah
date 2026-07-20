import asyncio
import httpx
import time
import statistics

# Gurukul Stability Stress Test
# ============================
# Goal: 100 consecutive requests to /voice/respond
# Concurrency: 5 simultaneous users

API_URL = "http://localhost:3000/api/v1/voice/respond"
TOTAL_REQUESTS = 100
CONCURRENCY = 5

async def send_request(client, i):
    payload = {
        "text": f"This is stability test request number {i}. Explain gravity briefly.",
        "language": "en",
        "return_audio": "true"
    }
    t0 = time.perf_counter()
    try:
        # We use data= because it's a Form endpoint
        resp = await client.post(API_URL, data=payload, timeout=30)
        latency = (time.perf_counter() - t0) * 1000
        if resp.status_code == 200:
            return True, latency
        else:
            return False, 0
    except Exception as e:
        print(f"Request {i} failed: {e}")
        return False, 0

async def run_test():
    print(f"Starting Stress Test: {TOTAL_REQUESTS} requests | Concurrency={CONCURRENCY}")
    
    latencies = []
    success_count = 0
    failure_count = 0
    
    async with httpx.AsyncClient() as client:
        # Use semaphore for concurrency control
        sem = asyncio.Semaphore(CONCURRENCY)
        
        async def sem_request(i):
            async with sem:
                success, latency = await send_request(client, i)
                return success, latency

            tasks = [sem_request(i) for i in range(TOTAL_REQUESTS)]
            results = await asyncio.gather(*tasks)
            
            for success, latency in results:
                if success:
                    success_count += 1
                    latencies.append(latency)
                else:
                    failure_count += 1

    print("\n--- Test Results ---")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print(f"Successes:      {success_count}")
    print(f"Failures:       {failure_count}")
    
    if latencies:
        print(f"Avg Latency:    {statistics.mean(latencies):.2f} ms")
        print(f"P95 Latency:    {statistics.quantiles(latencies, n=20)[18]:.2f} ms")
        print(f"Min/Max:        {min(latencies):.2f} / {max(latencies):.2f} ms")

if __name__ == "__main__":
    asyncio.run(run_test())
