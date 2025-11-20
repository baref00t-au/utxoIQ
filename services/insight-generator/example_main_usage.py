"""
Example usage of the insight-generator FastAPI application.

This script demonstrates how to:
1. Start the service
2. Check health status
3. Trigger a manual polling cycle
4. Monitor service statistics

Requirements:
- Service must be running (uvicorn src.main:app)
- BigQuery credentials configured
- AI provider configured
"""

import asyncio
import httpx


BASE_URL = "http://localhost:8080"


async def check_service_info():
    """Check service information."""
    print("=" * 60)
    print("Checking Service Information")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()


async def check_health():
    """Check service health."""
    print("=" * 60)
    print("Checking Service Health")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service is healthy")
            print(f"   Polling Active: {data['polling_active']}")
            print(f"   Poll Interval: {data['poll_interval_seconds']}s")
            print(f"   Confidence Threshold: {data['confidence_threshold']}")
            print(f"   AI Provider: {data['ai_provider']}")
            print(f"   Unprocessed Signals: {data['unprocessed_signals']}")
            print(f"   Project: {data['project_id']}")
            print(f"   Dataset: {data['dataset']}")
        else:
            print(f"❌ Service is unhealthy")
            print(f"   Response: {response.text}")
        print()


async def trigger_manual_cycle():
    """Trigger a manual polling cycle."""
    print("=" * 60)
    print("Triggering Manual Polling Cycle")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{BASE_URL}/trigger-cycle")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cycle completed successfully")
            print(f"   Correlation ID: {data['correlation_id']}")
            print(f"   Signal Groups: {data['signal_groups']}")
            print(f"   Signals Processed: {data['signals_processed']}")
            print(f"   Insights Generated: {data['insights_generated']}")
        else:
            print(f"❌ Cycle failed")
            print(f"   Response: {response.text}")
        print()


async def check_stats():
    """Check service statistics."""
    print("=" * 60)
    print("Checking Service Statistics")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/stats")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Service Statistics:")
            print(f"   Unprocessed Signals: {data['unprocessed_signals']}")
            print(f"   Stale Signals (>1h): {data['stale_signals']}")
            print(f"   Polling Active: {data['polling_active']}")
            print(f"   Poll Interval: {data['poll_interval_seconds']}s")
        else:
            print(f"❌ Failed to get stats")
            print(f"   Response: {response.text}")
        print()


async def monitor_service(duration_seconds: int = 30):
    """Monitor service for a period of time."""
    print("=" * 60)
    print(f"Monitoring Service for {duration_seconds} seconds")
    print("=" * 60)
    
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < duration_seconds:
        await check_stats()
        await asyncio.sleep(10)  # Check every 10 seconds
    
    print("Monitoring complete")


async def main():
    """Main example workflow."""
    print("\n" + "=" * 60)
    print("Insight Generator Service - Example Usage")
    print("=" * 60 + "\n")
    
    try:
        # 1. Check service info
        await check_service_info()
        
        # 2. Check health
        await check_health()
        
        # 3. Check initial stats
        await check_stats()
        
        # 4. Trigger a manual cycle
        print("Triggering a manual polling cycle...")
        await trigger_manual_cycle()
        
        # 5. Check stats after cycle
        await check_stats()
        
        # 6. Optional: Monitor for 30 seconds
        # Uncomment to enable monitoring
        # await monitor_service(duration_seconds=30)
        
        print("\n" + "=" * 60)
        print("Example Complete!")
        print("=" * 60)
        print("\nThe service is now running in the background.")
        print("It will automatically poll for signals every 10 seconds.")
        print("\nTo stop the service, press Ctrl+C in the terminal where it's running.")
        
    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to service")
        print("   Make sure the service is running:")
        print("   uvicorn src.main:app --host 0.0.0.0 --port 8080")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
