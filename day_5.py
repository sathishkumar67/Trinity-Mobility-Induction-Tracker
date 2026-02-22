import asyncio
import random
import redis.asyncio as redis
from prefect import flow, task

@task(retries=2, retry_delay_seconds=1)
async def fetch_data():
    print("   -> Fetching data from source...")
    if random.random() < 0.5:
        print("   -> ❌ Oops! Fetch failed. Prefect will retry...")
        raise ValueError("Random failure!")
    return "my_valuable_data"

@flow(log_prints=True)
async def local_redis_pipeline():
    client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    try:
        cache_key = "pipeline:latest_data"
        
        cached_data = await client.get(cache_key)
        
        if cached_data:
            print(f"✅ CACHE HIT: Found '{cached_data}' in Redis. Skipping fetch.")
            final_data = cached_data
        else:
            print("🐢 CACHE MISS: Data not in Redis. Running task...")
            final_data = await fetch_data()
            
            await client.setex(cache_key, 5, final_data)
            print(f"💾 SAVED: Data cached in Redis for 5 seconds.")

        await client.publish("system_alerts", f"Processed data: {final_data}")
        print("📢 PUB/SUB: Broadcasted completion message!")

    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(local_redis_pipeline())