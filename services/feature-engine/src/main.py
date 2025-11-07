"""
Feature Engine FastAPI application
Event-driven signal processing service
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio

from .config import settings
from .signal_processor import SignalProcessor
from .models import (
    Signal, BlockData, MempoolData, ExchangeFlowData,
    MinerTreasuryData, WhaleActivityData
)

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="utxoIQ Feature Engine",
    description="Signal computation and predictive analytics service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize signal processor
signal_processor = SignalProcessor()


# Request/Response models
class BlockProcessRequest(BaseModel):
    """Request model for block processing"""
    block_data: BlockData
    mempool_data: Optional[MempoolData] = None
    exchange_flows: Optional[List[ExchangeFlowData]] = None
    miner_data: Optional[List[MinerTreasuryData]] = None
    whale_data: Optional[List[WhaleActivityData]] = None


class SignalResponse(BaseModel):
    """Response model for signal generation"""
    signals: List[Signal]
    block_height: int
    processed_at: datetime
    signal_count: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime


# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with service information"""
    return HealthResponse(
        status="healthy",
        service="feature-engine",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="feature-engine",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


@app.post("/process-block", response_model=SignalResponse)
async def process_block(
    request: BlockProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Process a new block and generate signals
    
    This endpoint is triggered by new blockchain data events
    """
    try:
        logger.info(f"Processing block {request.block_data.height}")
        
        # Process block and generate signals
        signals = signal_processor.process_block(
            block_data=request.block_data,
            mempool_data=request.mempool_data,
            exchange_flows=request.exchange_flows,
            miner_data=request.miner_data,
            whale_data=request.whale_data
        )
        
        # Publish signals to Pub/Sub in background
        background_tasks.add_task(
            publish_signals,
            signals,
            request.block_data.height
        )
        
        return SignalResponse(
            signals=signals,
            block_height=request.block_data.height,
            processed_at=datetime.utcnow(),
            signal_count=len(signals)
        )
        
    except Exception as e:
        logger.error(f"Error processing block: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compute-mempool-signal", response_model=Signal)
async def compute_mempool_signal(
    mempool_data: MempoolData,
    historical_data: Optional[List[MempoolData]] = None
):
    """
    Compute mempool signal for given data
    """
    try:
        signal = signal_processor.compute_mempool_signals(
            mempool_data,
            historical_data
        )
        return signal
    except Exception as e:
        logger.error(f"Error computing mempool signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect-exchange-flow", response_model=Signal)
async def detect_exchange_flow(
    flow_data: ExchangeFlowData,
    historical_flows: Optional[List[ExchangeFlowData]] = None
):
    """
    Detect exchange flow anomalies
    """
    try:
        signal = signal_processor.detect_exchange_flows(
            flow_data,
            historical_flows
        )
        return signal
    except Exception as e:
        logger.error(f"Error detecting exchange flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-miner-treasury", response_model=Signal)
async def analyze_miner_treasury(
    miner_data: MinerTreasuryData,
    historical_data: Optional[List[MinerTreasuryData]] = None
):
    """
    Analyze miner treasury changes
    """
    try:
        signal = signal_processor.analyze_miner_treasury(
            miner_data,
            historical_data
        )
        return signal
    except Exception as e:
        logger.error(f"Error analyzing miner treasury: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/track-whale-accumulation", response_model=Signal)
async def track_whale_accumulation(
    whale_data: WhaleActivityData,
    historical_data: Optional[List[WhaleActivityData]] = None
):
    """
    Track whale accumulation patterns
    """
    try:
        signal = signal_processor.track_whale_accumulation(
            whale_data,
            historical_data
        )
        return signal
    except Exception as e:
        logger.error(f"Error tracking whale accumulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-predictive-signals", response_model=List[Signal])
async def generate_predictive_signals(
    mempool_data: MempoolData,
    historical_mempool: List[MempoolData],
    exchange_flows: List[ExchangeFlowData],
    current_flow: ExchangeFlowData
):
    """
    Generate predictive analytics signals
    """
    try:
        signals = signal_processor.generate_predictive_signals(
            mempool_data,
            historical_mempool,
            exchange_flows,
            current_flow
        )
        return signals
    except Exception as e:
        logger.error(f"Error generating predictive signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background tasks

async def publish_signals(signals: List[Signal], block_height: int):
    """
    Publish generated signals to Pub/Sub topic
    
    Args:
        signals: List of signals to publish
        block_height: Block height for the signals
    """
    try:
        logger.info(f"Publishing {len(signals)} signals for block {block_height}")
        
        # TODO: Implement Pub/Sub publishing
        # from google.cloud import pubsub_v1
        # publisher = pubsub_v1.PublisherClient()
        # topic_path = publisher.topic_path(settings.gcp_project_id, settings.pubsub_topic_signals)
        
        # for signal in signals:
        #     data = signal.json().encode('utf-8')
        #     future = publisher.publish(topic_path, data)
        #     future.result()
        
        logger.info(f"Successfully published {len(signals)} signals")
        
    except Exception as e:
        logger.error(f"Error publishing signals: {e}")


# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Feature Engine service starting up")
    logger.info(f"Confidence threshold: {settings.confidence_threshold}")
    logger.info(f"Model version: {settings.model_version}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Feature Engine service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
