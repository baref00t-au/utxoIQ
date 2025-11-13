"""
Alert evaluator handler for Cloud Function.

This module provides the business logic for evaluating alerts,
managing database connections, and coordinating with notification services.
"""
import logging
import os
import asyncio
from typing import Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class AlertEvaluatorHandler:
    """
    Handler for alert evaluation in Cloud Function context.
    
    This class manages database connections, initializes services,
    and coordinates alert evaluation.
    """
    
    def __init__(self):
        """Initialize handler with database and service connections."""
        # Get configuration from environment
        self.database_url = os.environ.get('DATABASE_URL')
        self.redis_url = os.environ.get('REDIS_URL')
        self.gcp_project_id = os.environ.get('GCP_PROJECT_ID')
        
        # Validate configuration
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        if not self.gcp_project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        
        logger.info("AlertEvaluatorHandler initialized")
    
    def evaluate_all_alerts(self) -> Dict[str, Any]:
        """
        Evaluate all enabled alerts synchronously.
        
        This method wraps the async evaluation logic for Cloud Function compatibility.
        
        Returns:
            Dictionary with evaluation summary
        """
        # Run async evaluation in event loop
        return asyncio.run(self._evaluate_all_alerts_async())
    
    async def _evaluate_all_alerts_async(self) -> Dict[str, Any]:
        """
        Evaluate all enabled alerts asynchronously.
        
        Returns:
            Dictionary with evaluation summary:
            - total_evaluated: Number of alerts evaluated
            - triggered: Number of alerts triggered
            - resolved: Number of alerts resolved
            - suppressed: Number of alerts suppressed
            - errors: Number of evaluation errors
        """
        # Create database engine
        engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        
        # Create session factory
        async_session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Initialize Redis client if URL provided
        redis_client = None
        if self.redis_url:
            try:
                redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                redis_client = None
        
        try:
            # Create database session
            async with async_session_factory() as session:
                # Import services here to avoid import issues
                from metrics_service_wrapper import MetricsServiceWrapper
                from notification_service_wrapper import NotificationServiceWrapper
                from alert_evaluator_wrapper import AlertEvaluatorWrapper
                
                # Initialize services
                metrics_service = MetricsServiceWrapper(
                    project_id=self.gcp_project_id,
                    redis_client=redis_client
                )
                
                notification_service = NotificationServiceWrapper()
                
                evaluator = AlertEvaluatorWrapper(
                    metrics_service=metrics_service,
                    db=session,
                    notification_service=notification_service
                )
                
                # Evaluate all alerts
                result = await evaluator.evaluate_all_alerts()
                
                return result
                
        finally:
            # Clean up connections
            await engine.dispose()
            if redis_client:
                await redis_client.close()
