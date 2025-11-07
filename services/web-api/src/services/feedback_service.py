"""Feedback service."""
import logging
from datetime import datetime
from ..models import UserFeedback, FeedbackCreate

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for managing user feedback."""
    
    async def create_feedback(
        self,
        insight_id: str,
        user_id: str,
        feedback_data: FeedbackCreate
    ) -> UserFeedback:
        """Create new feedback."""
        # TODO: Implement BigQuery insert
        logger.info(f"Creating feedback for insight {insight_id} from user {user_id}")
        return UserFeedback(
            id="feedback_placeholder",
            insight_id=insight_id,
            user_id=user_id,
            rating=feedback_data.rating,
            timestamp=datetime.utcnow(),
            comment=feedback_data.comment
        )
