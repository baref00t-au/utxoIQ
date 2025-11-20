"""
AI-powered Bitcoin Insight Generator Service.

This service polls BigQuery for unprocessed signals and generates insights using AI.

Main responsibilities:
- Poll for unprocessed signals every 10 seconds
- Generate insights using configured AI provider
- Persist insights to BigQuery
- Mark signals as processed

Requirements: 3.1, 3.2, 3.5, 5.2
"""
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from google.cloud import bigquery

from .signal_polling import SignalPollingModule
from .insight_generation import InsightGenerationModule
from .insight_persistence import InsightPersistenceModule
from .ai_provider import get_configured_provider, AIProviderError


# Configuration from environment
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "utxoiq-dev")
DATASET_INTEL = os.getenv("DATASET_INTEL", "intel")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global state for background task
polling_task: Optional[asyncio.Task] = None
is_running = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    
    Starts background polling task on startup and stops it on shutdown.
    """
    global polling_task, is_running
    
    logger.info("Starting insight-generator service")
    
    # Start background polling task
    is_running = True
    polling_task = asyncio.create_task(run_polling_loop())
    
    logger.info("Background polling task started")
    
    yield
    
    # Shutdown: stop background task
    logger.info("Shutting down insight-generator service")
    is_running = False
    
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            logger.info("Polling task cancelled")
    
    logger.info("Shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="utxoIQ Insight Generator",
    description="AI-powered Bitcoin blockchain insight generation service",
    version="1.0.0",
    lifespan=lifespan
)


class InsightGeneratorService:
    """
    Main service class that wires together all insight generation components.
    
    Requirements: 5.2
    """
    
    def __init__(self):
        """Initialize all modules with proper configuration."""
        logger.info("Initializing InsightGeneratorService")
        
        # Initialize BigQuery client
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        logger.info(f"BigQuery client initialized for project: {PROJECT_ID}")
        
        # Initialize AI provider based on configuration
        try:
            self.ai_provider = get_configured_provider()
            logger.info(
                f"AI provider initialized: {self.ai_provider.__class__.__name__}"
            )
        except AIProviderError as e:
            logger.error(f"Failed to initialize AI provider: {e}")
            raise
        
        # Initialize Signal Polling Module
        self.signal_polling = SignalPollingModule(
            bigquery_client=self.bq_client,
            project_id=PROJECT_ID,
            dataset_id=DATASET_INTEL,
            confidence_threshold=CONFIDENCE_THRESHOLD
        )
        logger.info("Signal Polling Module initialized")
        
        # Initialize Insight Generation Module
        self.insight_generation = InsightGenerationModule(
            ai_provider=self.ai_provider
        )
        logger.info("Insight Generation Module initialized")
        
        # Initialize Insight Persistence Module
        self.insight_persistence = InsightPersistenceModule(
            bigquery_client=self.bq_client,
            project_id=PROJECT_ID,
            dataset_id=DATASET_INTEL
        )
        logger.info("Insight Persistence Module initialized")
        
        logger.info("InsightGeneratorService initialization complete")
    
    async def process_signal_group(
        self,
        signal_group,
        correlation_id: str
    ) -> int:
        """
        Process a group of signals and generate insights.
        
        Args:
            signal_group: SignalGroup containing signals to process
            correlation_id: Correlation ID for request tracing
            
        Returns:
            Number of insights successfully generated
            
        Requirements: 3.1, 3.2, 3.5
        """
        logger.info(
            f"Processing signal group: {signal_group.signal_type} "
            f"at block {signal_group.block_height} "
            f"({len(signal_group.signals)} signals)",
            extra={
                "correlation_id": correlation_id,
                "signal_type": signal_group.signal_type,
                "block_height": signal_group.block_height,
                "signal_count": len(signal_group.signals)
            }
        )
        
        insights_generated = 0
        
        for signal in signal_group.signals:
            try:
                # Generate insight from signal
                insight = await self.insight_generation.generate_insight(signal)
                
                if not insight:
                    logger.warning(
                        f"Failed to generate insight for signal {signal['signal_id']}",
                        extra={
                            "correlation_id": correlation_id,
                            "signal_id": signal['signal_id']
                        }
                    )
                    continue
                
                # Persist insight to BigQuery
                result = await self.insight_persistence.persist_insight(
                    insight,
                    correlation_id
                )
                
                if result.success:
                    # Mark signal as processed
                    await self.signal_polling.mark_signal_processed(
                        signal['signal_id']
                    )
                    insights_generated += 1
                    
                    logger.info(
                        f"Successfully generated and persisted insight "
                        f"{result.insight_id} for signal {signal['signal_id']}",
                        extra={
                            "correlation_id": correlation_id,
                            "signal_id": signal['signal_id'],
                            "insight_id": result.insight_id
                        }
                    )
                else:
                    logger.error(
                        f"Failed to persist insight for signal {signal['signal_id']}: "
                        f"{result.error}",
                        extra={
                            "correlation_id": correlation_id,
                            "signal_id": signal['signal_id'],
                            "error": result.error
                        }
                    )
                    
            except Exception as e:
                logger.error(
                    f"Error processing signal {signal['signal_id']}: {e}",
                    extra={
                        "correlation_id": correlation_id,
                        "signal_id": signal['signal_id'],
                        "error": str(e)
                    }
                )
        
        return insights_generated
    
    async def run_polling_cycle(self) -> dict:
        """
        Run one polling cycle: poll signals, generate insights, mark as processed.
        
        Returns:
            Dictionary with cycle statistics
            
        Requirements: 3.1, 3.2, 3.5
        """
        correlation_id = str(uuid.uuid4())
        
        logger.info(
            "Starting polling cycle",
            extra={"correlation_id": correlation_id}
        )
        
        try:
            # Poll for unprocessed signals
            signal_groups = await self.signal_polling.poll_unprocessed_signals()
            
            if not signal_groups:
                logger.debug(
                    "No unprocessed signals found",
                    extra={"correlation_id": correlation_id}
                )
                return {
                    "correlation_id": correlation_id,
                    "signal_groups": 0,
                    "signals_processed": 0,
                    "insights_generated": 0
                }
            
            # Process each signal group
            total_insights = 0
            total_signals = sum(len(group.signals) for group in signal_groups)
            
            for signal_group in signal_groups:
                insights = await self.process_signal_group(
                    signal_group,
                    correlation_id
                )
                total_insights += insights
            
            logger.info(
                f"Polling cycle complete: processed {total_signals} signals, "
                f"generated {total_insights} insights",
                extra={
                    "correlation_id": correlation_id,
                    "signal_groups": len(signal_groups),
                    "signals_processed": total_signals,
                    "insights_generated": total_insights
                }
            )
            
            return {
                "correlation_id": correlation_id,
                "signal_groups": len(signal_groups),
                "signals_processed": total_signals,
                "insights_generated": total_insights
            }
            
        except Exception as e:
            logger.error(
                f"Error in polling cycle: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e)
                }
            )
            return {
                "correlation_id": correlation_id,
                "error": str(e)
            }


# Global service instance
service: Optional[InsightGeneratorService] = None


def get_service() -> InsightGeneratorService:
    """Get or create service instance."""
    global service
    if service is None:
        service = InsightGeneratorService()
    return service


async def run_polling_loop():
    """
    Background task that polls for unprocessed signals every 10 seconds.
    
    Requirements: 3.1, 3.2
    """
    global is_running
    
    logger.info(
        f"Starting polling loop (interval: {POLL_INTERVAL_SECONDS} seconds)"
    )
    
    # Initialize service
    svc = get_service()
    
    while is_running:
        try:
            # Run one polling cycle
            await svc.run_polling_cycle()
            
            # Wait for next cycle
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            
        except asyncio.CancelledError:
            logger.info("Polling loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in polling loop: {e}")
            # Wait before retrying
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    
    logger.info("Polling loop stopped")


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "utxoIQ Insight Generator",
        "version": "1.0.0",
        "status": "running" if is_running else "stopped"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns service health status and configuration.
    
    Requirements: 3.1
    """
    try:
        svc = get_service()
        
        # Check if we can query BigQuery
        unprocessed_count = await svc.signal_polling.get_unprocessed_signal_count()
        
        return {
            "status": "healthy",
            "polling_active": is_running,
            "poll_interval_seconds": POLL_INTERVAL_SECONDS,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "ai_provider": svc.ai_provider.__class__.__name__,
            "unprocessed_signals": unprocessed_count,
            "project_id": PROJECT_ID,
            "dataset": DATASET_INTEL
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.post("/trigger-cycle")
async def trigger_cycle():
    """
    Manually trigger a polling cycle.
    
    Useful for testing and debugging.
    """
    try:
        svc = get_service()
        result = await svc.run_polling_cycle()
        return result
    except Exception as e:
        logger.error(f"Error triggering cycle: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger cycle: {str(e)}"
        )


@app.get("/stats")
async def get_stats():
    """Get service statistics."""
    try:
        svc = get_service()
        
        unprocessed_count = await svc.signal_polling.get_unprocessed_signal_count()
        stale_signals = await svc.signal_polling.get_stale_signals(max_age_hours=1)
        
        return {
            "unprocessed_signals": unprocessed_count,
            "stale_signals": len(stale_signals),
            "polling_active": is_running,
            "poll_interval_seconds": POLL_INTERVAL_SECONDS
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=False,
        log_level="info"
    )
