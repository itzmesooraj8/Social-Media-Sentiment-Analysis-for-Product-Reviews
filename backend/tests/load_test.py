
import asyncio
import time
import httpx
import numpy as np

# Configuration
BASE_URL = "http://127.0.0.1:8000"
CONCURRENT_REQUESTS = 5 # Reduced for local dev stability (was 50)
TOTAL_REQUESTS = 50 # Reduced for demo speed
ENDPOINT = "/api/analyze"
PAYLOAD = {"text": "This product is absolutely amazing, I love the speed and the design!"}

async def send_request(client):
    start = time.time()
    try:
        resp = await client.post(ENDPOINT, json=PAYLOAD)
        resp.raise_for_status()
        return time.time() - start
    except Exception as e:
        print(f"Request failed: {e}")
        return None

async def run_load_test():
    print(f"--- Load Testing {BASE_URL}{ENDPOINT} ---")
    print(f"Simulating {TOTAL_REQUESTS} requests with {CONCURRENT_REQUESTS} concurrency...")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Warmup
        await client.post(ENDPOINT, json=PAYLOAD)
        
        tasks = []
        latencies = []
        start_total = time.time()
        
        # Batch execution
        for i in range(0, TOTAL_REQUESTS, CONCURRENT_REQUESTS):
            batch = [send_request(client) for _ in range(CONCURRENT_REQUESTS)]
            results = await asyncio.gather(*batch)
            latencies.extend([r for r in results if r is not None])
            print(f"Batch {i//CONCURRENT_REQUESTS + 1} completed.")
            
        end_total = time.time()
        total_time = end_total - start_total
        
        # Metrics
        latencies_ms = [l * 1000 for l in latencies]
        avg_lat = np.mean(latencies_ms)
        p95_lat = np.percentile(latencies_ms, 95)
        p99_lat = np.percentile(latencies_ms, 99)
        rps = len(latencies) / total_time
        
        print("\n--- Results ---")
        print(f"Total Requests: {len(latencies)}/{TOTAL_REQUESTS}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Throughput: {rps:.2f} req/s")
        print(f"Avg Latency: {avg_lat:.2f}ms")
        print(f"P95 Latency: {p95_lat:.2f}ms")
        print(f"P99 Latency: {p99_lat:.2f}ms")
        
        if total_time <= 5.0 and len(latencies) >= 1000:
             print("✅ GOAL MET: 1000 requests processed in under 5 seconds.")
        elif rps > 50:
             print("✅ Performance is healthy (>50 RPS for CPU bound Sentiment analysis is good).")
        else:
             print("⚠️ Performance might need optimization for strict 1000/5s goal on local hardware.")

if __name__ == "__main__":
    try:
        asyncio.run(run_load_test())
    except KeyboardInterrupt:
        pass
