#!/usr/bin/env python3
"""
Integration test script to verify all components are working together
"""

import requests
import json
import time
from websocket import create_connection
import sys

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

def test_api_health():
    """Test API health endpoint"""
    print("Testing API health...")
    try:
        response = requests.get(f"{API_URL}/health")
        assert response.status_code == 200
        print("✓ API health check passed")
        return True
    except Exception as e:
        print(f"✗ API health check failed: {e}")
        return False

def test_monitoring_status():
    """Test monitoring status endpoint"""
    print("\nTesting monitoring status...")
    try:
        response = requests.get(f"{API_URL}/api/v1/monitoring/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "processing_metrics" in data
        print("✓ Monitoring status endpoint passed")
        print(f"  System status: {data['status']}")
        print(f"  Services: {len(data['services'])}")
        return True
    except Exception as e:
        print(f"✗ Monitoring status failed: {e}")
        return False

def test_signal_metrics():
    """Test signal metrics endpoint"""
    print("\nTesting signal metrics...")
    try:
        response = requests.get(f"{API_URL}/api/v1/monitoring/metrics/signals")
        assert response.status_code == 200
        data = response.json()
        assert "total_signals" in data
        assert "signals_by_category" in data
        print("✓ Signal metrics endpoint passed")
        print(f"  Total signals: {data['total_signals']}")
        return True
    except Exception as e:
        print(f"✗ Signal metrics failed: {e}")
        return False

def test_insight_metrics():
    """Test insight metrics endpoint"""
    print("\nTesting insight metrics...")
    try:
        response = requests.get(f"{API_URL}/api/v1/monitoring/metrics/insights")
        assert response.status_code == 200
        data = response.json()
        assert "insights_generated" in data
        assert "avg_confidence" in data
        print("✓ Insight metrics endpoint passed")
        print(f"  Insights generated: {data['insights_generated']}")
        return True
    except Exception as e:
        print(f"✗ Insight metrics failed: {e}")
        return False

def test_feedback_rate():
    """Test feedback rate endpoint"""
    print("\nTesting feedback rate...")
    try:
        response = requests.post(
            f"{API_URL}/api/v1/feedback/insights/test123/rate",
            json={"rating": 5, "comment": "Test comment"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("✓ Feedback rate endpoint passed")
        return True
    except Exception as e:
        print(f"✗ Feedback rate failed: {e}")
        return False

def test_feedback_stats():
    """Test feedback stats endpoint"""
    print("\nTesting feedback stats...")
    try:
        response = requests.get(f"{API_URL}/api/v1/feedback/insights/test123/stats")
        assert response.status_code == 200
        data = response.json()
        assert "insight_id" in data
        assert "total_ratings" in data
        print("✓ Feedback stats endpoint passed")
        return True
    except Exception as e:
        print(f"✗ Feedback stats failed: {e}")
        return False

def test_websocket_monitoring():
    """Test WebSocket monitoring connection"""
    print("\nTesting WebSocket monitoring...")
    try:
        ws = create_connection(f"{WS_URL}/ws/monitoring")
        
        # Send subscribe message
        ws.send(json.dumps({"type": "subscribe"}))
        
        # Wait for response
        result = ws.recv()
        data = json.loads(result)
        
        # Send ping
        ws.send(json.dumps({"type": "ping", "timestamp": "2024-01-15T10:30:00Z"}))
        
        # Wait for pong
        result = ws.recv()
        data = json.loads(result)
        assert data["type"] == "pong"
        
        ws.close()
        print("✓ WebSocket monitoring passed")
        return True
    except Exception as e:
        print(f"✗ WebSocket monitoring failed: {e}")
        return False

def test_backfill_endpoints():
    """Test backfill endpoints"""
    print("\nTesting backfill endpoints...")
    try:
        response = requests.get(f"{API_URL}/api/v1/monitoring/backfill")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print("✓ Backfill list endpoint passed")
        return True
    except Exception as e:
        print(f"✗ Backfill endpoints failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("utxoIQ Platform Integration Tests")
    print("=" * 60)
    
    tests = [
        test_api_health,
        test_monitoring_status,
        test_signal_metrics,
        test_insight_metrics,
        test_feedback_rate,
        test_feedback_stats,
        test_backfill_endpoints,
        test_websocket_monitoring,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
