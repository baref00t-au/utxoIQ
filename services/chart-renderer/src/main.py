"""
Chart Renderer Service - FastAPI Application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from .models import (
    MempoolChartRequest,
    ExchangeChartRequest,
    MinerChartRequest,
    WhaleChartRequest,
    PredictiveChartRequest,
    ChartResponse
)
from .renderers import (
    MempoolRenderer,
    ExchangeRenderer,
    MinerRenderer,
    WhaleRenderer,
    PredictiveRenderer
)
from .storage import chart_storage
from .config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="utxoIQ Chart Renderer",
    description="AI-powered chart generation service for Bitcoin blockchain insights",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize renderers
mempool_renderer = MempoolRenderer()
exchange_renderer = ExchangeRenderer()
miner_renderer = MinerRenderer()
whale_renderer = WhaleRenderer()
predictive_renderer = PredictiveRenderer()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "chart-renderer",
        "version": "1.0.0"
    }


@app.post("/render/mempool", response_model=ChartResponse)
async def render_mempool_chart(request: MempoolChartRequest):
    """
    Generate mempool fee distribution chart with quantile visualization
    
    Args:
        request: Mempool chart request data
        
    Returns:
        Chart response with GCS URL
    """
    try:
        logger.info(f"Rendering mempool chart for block {request.block_height}")
        
        # Render chart
        chart_bytes = mempool_renderer.render(request)
        
        # Upload to GCS
        signed_url, chart_path, size_bytes = chart_storage.upload_chart(
            chart_bytes, "mempool"
        )
        
        width, height = mempool_renderer.get_figure_size(request.size)
        
        return ChartResponse(
            chart_url=signed_url,
            chart_path=chart_path,
            width=width,
            height=height,
            size_bytes=size_bytes
        )
        
    except Exception as e:
        logger.error(f"Failed to render mempool chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/render/exchange", response_model=ChartResponse)
async def render_exchange_chart(request: ExchangeChartRequest):
    """
    Generate exchange flow chart with timeline and volume indicators
    
    Args:
        request: Exchange chart request data
        
    Returns:
        Chart response with GCS URL
    """
    try:
        logger.info(f"Rendering exchange chart for {request.entity_name}")
        
        # Render chart
        chart_bytes = exchange_renderer.render(request)
        
        # Upload to GCS
        signed_url, chart_path, size_bytes = chart_storage.upload_chart(
            chart_bytes, "exchange"
        )
        
        width, height = exchange_renderer.get_figure_size(request.size)
        
        return ChartResponse(
            chart_url=signed_url,
            chart_path=chart_path,
            width=width,
            height=height,
            size_bytes=size_bytes
        )
        
    except Exception as e:
        logger.error(f"Failed to render exchange chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/render/miner", response_model=ChartResponse)
async def render_miner_chart(request: MinerChartRequest):
    """
    Generate miner treasury chart with balance change visualization
    
    Args:
        request: Miner chart request data
        
    Returns:
        Chart response with GCS URL
    """
    try:
        logger.info(f"Rendering miner chart for {request.entity_name}")
        
        # Render chart
        chart_bytes = miner_renderer.render(request)
        
        # Upload to GCS
        signed_url, chart_path, size_bytes = chart_storage.upload_chart(
            chart_bytes, "miner"
        )
        
        width, height = miner_renderer.get_figure_size(request.size)
        
        return ChartResponse(
            chart_url=signed_url,
            chart_path=chart_path,
            width=width,
            height=int(height * 1.5),  # Adjusted for dual-panel layout
            size_bytes=size_bytes
        )
        
    except Exception as e:
        logger.error(f"Failed to render miner chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/render/whale", response_model=ChartResponse)
async def render_whale_chart(request: WhaleChartRequest):
    """
    Generate whale accumulation chart with streak highlighting
    
    Args:
        request: Whale chart request data
        
    Returns:
        Chart response with GCS URL
    """
    try:
        logger.info(f"Rendering whale chart for {request.address[:8]}...")
        
        # Render chart
        chart_bytes = whale_renderer.render(request)
        
        # Upload to GCS
        signed_url, chart_path, size_bytes = chart_storage.upload_chart(
            chart_bytes, "whale"
        )
        
        width, height = whale_renderer.get_figure_size(request.size)
        
        return ChartResponse(
            chart_url=signed_url,
            chart_path=chart_path,
            width=width,
            height=int(height * 1.5),  # Adjusted for dual-panel layout
            size_bytes=size_bytes
        )
        
    except Exception as e:
        logger.error(f"Failed to render whale chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/render/predictive", response_model=ChartResponse)
async def render_predictive_chart(request: PredictiveChartRequest):
    """
    Generate predictive signal chart with confidence intervals
    
    Args:
        request: Predictive chart request data
        
    Returns:
        Chart response with GCS URL
    """
    try:
        logger.info(f"Rendering predictive chart for {request.signal_type}")
        
        # Render chart
        chart_bytes = predictive_renderer.render(request)
        
        # Upload to GCS
        signed_url, chart_path, size_bytes = chart_storage.upload_chart(
            chart_bytes, "predictive"
        )
        
        width, height = predictive_renderer.get_figure_size(request.size)
        
        return ChartResponse(
            chart_url=signed_url,
            chart_path=chart_path,
            width=width,
            height=height,
            size_bytes=size_bytes
        )
        
    except Exception as e:
        logger.error(f"Failed to render predictive chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
