"""
Cloud Function for evaluating monitoring alerts.

This function is triggered by Cloud Scheduler every 60 seconds to evaluate
all enabled alert configurations against current metrics.
"""
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def evaluate_alerts(request=None) -> tuple[Dict[str, Any], int]:
    """
    Cloud Function entry point for alert evaluation.
    
    This function is triggered by Cloud Scheduler and evaluates all enabled
    alert configurations. It implements idempotency to prevent duplicate alerts.
    
    Args:
        request: Flask request object (unused for scheduled functions)
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    execution_id = datetime.utcnow().isoformat()
    logger.info(f"Starting alert evaluation - execution_id: {execution_id}")
    
    try:
        # Import dependencies here to avoid cold start issues
        from alert_evaluator_handler import AlertEvaluatorHandler
        
        # Initialize handler
        handler = AlertEvaluatorHandler()
        
        # Evaluate all alerts
        result = handler.evaluate_all_alerts()
        
        # Log summary
        logger.info(
            f"Alert evaluation complete - execution_id: {execution_id}, "
            f"evaluated: {result['total_evaluated']}, "
            f"triggered: {result['triggered']}, "
            f"resolved: {result['resolved']}, "
            f"suppressed: {result['suppressed']}, "
            f"errors: {result['errors']}"
        )
        
        # Return success response
        response = {
            "status": "success",
            "execution_id": execution_id,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": result
        }
        
        return response, 200
        
    except Exception as e:
        logger.error(
            f"Alert evaluation failed - execution_id: {execution_id}, error: {e}",
            exc_info=True
        )
        
        # Return error response
        response = {
            "status": "error",
            "execution_id": execution_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        
        return response, 500


# For local testing
if __name__ == "__main__":
    print("Testing alert evaluator function...")
    result, status = evaluate_alerts()
    print(f"Status: {status}")
    print(f"Result: {result}")
