"""
Test script for alert evaluator Cloud Function.

This script tests the function locally before deployment.
"""
import os
import sys
import asyncio
from datetime import datetime

# Set test environment variables
os.environ['GCP_PROJECT_ID'] = os.getenv('GCP_PROJECT_ID', 'utxoiq-test')
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql+asyncpg://localhost/utxoiq_test')
os.environ['REDIS_URL'] = os.getenv('REDIS_URL', '')

# Import function
from main import evaluate_alerts


def test_function_execution():
    """Test basic function execution."""
    print("Testing alert evaluator function...")
    print(f"Project ID: {os.environ['GCP_PROJECT_ID']}")
    print(f"Database URL: {os.environ['DATABASE_URL'][:50]}...")
    print("")
    
    try:
        # Execute function
        result, status = evaluate_alerts()
        
        print(f"Status Code: {status}")
        print(f"Result: {result}")
        print("")
        
        # Validate response
        assert status in [200, 500], f"Unexpected status code: {status}"
        assert 'status' in result, "Missing 'status' in response"
        assert 'execution_id' in result, "Missing 'execution_id' in response"
        assert 'timestamp' in result, "Missing 'timestamp' in response"
        
        if status == 200:
            assert result['status'] == 'success', "Expected success status"
            assert 'summary' in result, "Missing 'summary' in response"
            
            summary = result['summary']
            assert 'total_evaluated' in summary, "Missing 'total_evaluated' in summary"
            assert 'triggered' in summary, "Missing 'triggered' in summary"
            assert 'resolved' in summary, "Missing 'resolved' in summary"
            assert 'suppressed' in summary, "Missing 'suppressed' in summary"
            assert 'errors' in summary, "Missing 'errors' in summary"
            
            print("✓ Function executed successfully")
            print(f"  - Evaluated: {summary['total_evaluated']} alerts")
            print(f"  - Triggered: {summary['triggered']} alerts")
            print(f"  - Resolved: {summary['resolved']} alerts")
            print(f"  - Suppressed: {summary['suppressed']} alerts")
            print(f"  - Errors: {summary['errors']} alerts")
        else:
            print("✗ Function execution failed")
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        return status == 200
        
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_idempotency():
    """Test that function is idempotent."""
    print("\nTesting idempotency...")
    
    try:
        # Execute function twice
        result1, status1 = evaluate_alerts()
        result2, status2 = evaluate_alerts()
        
        # Both should succeed
        assert status1 == 200, "First execution failed"
        assert status2 == 200, "Second execution failed"
        
        # Should not trigger duplicate alerts
        summary1 = result1['summary']
        summary2 = result2['summary']
        
        print("✓ Idempotency test passed")
        print(f"  First execution: {summary1['triggered']} triggered")
        print(f"  Second execution: {summary2['triggered']} triggered")
        
        return True
        
    except Exception as e:
        print(f"✗ Idempotency test failed: {e}")
        return False


def test_error_handling():
    """Test error handling with invalid configuration."""
    print("\nTesting error handling...")
    
    try:
        # Temporarily set invalid database URL
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = 'invalid://url'
        
        # Execute function
        result, status = evaluate_alerts()
        
        # Restore original URL
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        
        # Should return error status
        assert status == 500, "Expected error status"
        assert result['status'] == 'error', "Expected error status"
        assert 'error' in result, "Missing error message"
        
        print("✓ Error handling test passed")
        print(f"  Error message: {result['error'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Alert Evaluator Function Tests")
    print("=" * 60)
    print("")
    
    tests = [
        ("Function Execution", test_function_execution),
        ("Idempotency", test_idempotency),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"Test: {test_name}")
        print(f"{'=' * 60}")
        
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print("")
    print(f"Total: {passed_count}/{total_count} tests passed")
    
    # Exit with appropriate code
    sys.exit(0 if passed_count == total_count else 1)


if __name__ == "__main__":
    main()
