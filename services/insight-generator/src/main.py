"""
Main FastAPI application for Insight Generator service
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import os

from .generators.insight_generator import InsightGenerator, Insight
from .feedback.feedback_processor import FeedbackProcessor, UserFeedback, FeedbackRating

# Initialize FastAPI app
app = FastAPI(
    title="utxoIQ Insight Generator",
    description="AI-powered Bitcoin blockchain insight generation service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
insight_generator = InsightGenerator(
    model_version=os.getenv("MODEL_VERSION", "1.0.0")
)
feedback_processor = FeedbackProcessor()


# Request/Response models
class GenerateInsightRequest(BaseModel):
    """Request model for insight generation"""
    signal_data: Dict[str, Any] = Field(..., description="Raw signal data")
    signal_type: str = Field(..., pattern="^(mempool|exchange|miner|whale|predictive)$")
    chart_url: Optional[str] = Field(None, description="Optional chart URL")


class InsightResponse(BaseModel):
    """Response model for generated insight"""
    id: str
    signal_type: str
    headline: str
    summary: str
    confidence: float
    timestamp: str
    block_height: int
    evidence: List[Dict[str, Any]]
    chart_url: Optional[str]
    tags: List[str]
    explainability: Optional[Dict[str, Any]]
    accuracy_rating: Optional[float]
    is_predictive: bool


class FeedbackRequest(BaseModel):
    """Request model for user feedback"""
    insight_id: str = Field(..., description="Insight ID")
    user_id: str = Field(..., description="User ID")
    rating: str = Field(..., pattern="^(useful|not_useful)$")
    comment: Optional[str] = Field(None, max_length=500)


class AccuracyRatingResponse(BaseModel):
    """Response model for accuracy rating"""
    insight_id: str
    total_feedback: int
    useful_count: int
    not_useful_count: int
    accuracy_score: float


class ModelAccuracyResponse(BaseModel):
    """Response model for model accuracy"""
    model_version: str
    signal_type: str
    total_insights: int
    total_feedback: int
    accuracy_score: float
    period_start: str
    period_end: str


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "insight-generator",
        "version": "1.0.0"
    }


# Insight generation endpoint
@app.post("/generate", response_model=InsightResponse, status_code=status.HTTP_201_CREATED)
async def generate_insight(request: GenerateInsightRequest):
    """
    Generate an AI-powered insight from signal data
    
    Args:
        request: GenerateInsightRequest with signal data
        
    Returns:
        InsightResponse with generated insight
        
    Raises:
        HTTPException: If insight generation fails
    """
    try:
        insight = insight_generator.generate_insight(
            signal_data=request.signal_data,
            signal_type=request.signal_type,
            chart_url=request.chart_url
        )
        
        if not insight:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to generate insight. Confidence too low or quiet mode active."
            )
        
        return InsightResponse(
            id=insight.id,
            signal_type=insight.signal_type,
            headline=insight.headline,
            summary=insight.summary,
            confidence=insight.confidence,
            timestamp=insight.timestamp.isoformat(),
            block_height=insight.block_height,
            evidence=[e.dict() for e in insight.evidence],
            chart_url=insight.chart_url,
            tags=insight.tags,
            explainability=insight.explainability.to_dict() if insight.explainability else None,
            accuracy_rating=insight.accuracy_rating,
            is_predictive=insight.is_predictive
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error generating insight: {str(e)}"
        )


# Feedback submission endpoint
@app.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback for an insight
    
    Args:
        request: FeedbackRequest with feedback data
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If feedback submission fails
    """
    try:
        feedback = UserFeedback(
            insight_id=request.insight_id,
            user_id=request.user_id,
            rating=FeedbackRating(request.rating),
            timestamp=datetime.now(),
            comment=request.comment
        )
        
        success = feedback_processor.store_feedback(feedback)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store feedback"
            )
        
        return {
            "message": "Feedback submitted successfully",
            "insight_id": request.insight_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error submitting feedback: {str(e)}"
        )


# Accuracy rating endpoint
@app.get("/insights/{insight_id}/accuracy", response_model=AccuracyRatingResponse)
async def get_accuracy_rating(insight_id: str):
    """
    Get aggregate accuracy rating for an insight
    
    Args:
        insight_id: Insight ID
        
    Returns:
        AccuracyRatingResponse with rating data
        
    Raises:
        HTTPException: If no feedback exists
    """
    try:
        rating = feedback_processor.calculate_accuracy_rating(insight_id)
        
        if not rating:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No feedback found for this insight"
            )
        
        return AccuracyRatingResponse(
            insight_id=rating.insight_id,
            total_feedback=rating.total_feedback,
            useful_count=rating.useful_count,
            not_useful_count=rating.not_useful_count,
            accuracy_score=rating.accuracy_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error getting accuracy rating: {str(e)}"
        )


# Model accuracy endpoint
@app.get("/models/{model_version}/accuracy", response_model=ModelAccuracyResponse)
async def get_model_accuracy(
    model_version: str,
    signal_type: Optional[str] = None,
    days: int = 30
):
    """
    Get accuracy metrics for a model version
    
    Args:
        model_version: Model version string
        signal_type: Optional signal type filter
        days: Number of days to look back (default: 30)
        
    Returns:
        ModelAccuracyResponse with accuracy metrics
        
    Raises:
        HTTPException: If insufficient data
    """
    try:
        accuracy = feedback_processor.get_model_accuracy(
            model_version=model_version,
            signal_type=signal_type,
            days=days
        )
        
        if not accuracy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insufficient data for this model version"
            )
        
        return ModelAccuracyResponse(
            model_version=accuracy.model_version,
            signal_type=accuracy.signal_type,
            total_insights=accuracy.total_insights,
            total_feedback=accuracy.total_feedback,
            accuracy_score=accuracy.accuracy_score,
            period_start=accuracy.period_start.isoformat(),
            period_end=accuracy.period_end.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error getting model accuracy: {str(e)}"
        )


# Accuracy leaderboard endpoint
@app.get("/leaderboard", response_model=List[ModelAccuracyResponse])
async def get_accuracy_leaderboard(limit: int = 10, days: int = 30):
    """
    Get public accuracy leaderboard by model version
    
    Args:
        limit: Maximum number of results (default: 10)
        days: Number of days to look back (default: 30)
        
    Returns:
        List of ModelAccuracyResponse sorted by accuracy
    """
    try:
        leaderboard = feedback_processor.get_accuracy_leaderboard(
            limit=limit,
            days=days
        )
        
        return [
            ModelAccuracyResponse(
                model_version=entry.model_version,
                signal_type=entry.signal_type,
                total_insights=entry.total_insights,
                total_feedback=entry.total_feedback,
                accuracy_score=entry.accuracy_score,
                period_start=entry.period_start.isoformat(),
                period_end=entry.period_end.isoformat()
            )
            for entry in leaderboard
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error getting leaderboard: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
