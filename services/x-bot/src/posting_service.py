"""Service for composing and posting tweets."""
import logging
from typing import Optional, List
from .models import Insight, TweetData, PostResult
from .x_client import XClient
from .redis_client import RedisClient
from .api_client import APIClient
from .config import settings

logger = logging.getLogger(__name__)


class PostingService:
    """Service for managing tweet composition and posting."""
    
    def __init__(self):
        """Initialize posting service."""
        self.x_client = XClient()
        self.redis_client = RedisClient()
        self.api_client = APIClient()
        logger.info("Posting service initialized")
    
    def compose_tweet(self, insight: Insight) -> str:
        """
        Compose tweet text from insight.
        
        Args:
            insight: Insight object
            
        Returns:
            Tweet text (max 280 characters)
        """
        # Start with headline
        tweet = insight.headline
        
        # Add confidence indicator
        confidence_pct = int(insight.confidence * 100)
        confidence_emoji = "🟢" if confidence_pct >= 85 else "🟡"
        
        # Add block height context
        block_info = f"\n\n{confidence_emoji} Confidence: {confidence_pct}%"
        block_info += f"\n📦 Block: {insight.block_height}"
        
        # Add link to full details
        detail_link = f"\n\n🔗 utxoiq.com/insight/{insight.id}"
        
        # Construct full tweet
        full_tweet = tweet + block_info + detail_link
        
        # Ensure it fits in 280 characters
        if len(full_tweet) > 280:
            # Truncate headline to fit
            max_headline_length = 280 - len(block_info) - len(detail_link) - 3  # 3 for "..."
            tweet = insight.headline[:max_headline_length] + "..."
            full_tweet = tweet + block_info + detail_link
        
        return full_tweet
    
    def should_post_insight(self, insight: Insight) -> tuple[bool, str]:
        """
        Determine if an insight should be posted.
        
        Args:
            insight: Insight object
            
        Returns:
            Tuple of (should_post, reason)
        """
        # Check confidence threshold
        if insight.confidence < settings.confidence_threshold:
            return False, f"Confidence {insight.confidence} below threshold {settings.confidence_threshold}"
        
        # Check if already posted
        if self.redis_client.is_insight_posted(insight.id):
            return False, f"Insight {insight.id} already posted"
        
        # Check if signal type was recently posted (duplicate prevention)
        if self.redis_client.is_signal_recently_posted(insight.signal_type.value):
            return False, f"Signal type {insight.signal_type.value} posted within duplicate prevention window"
        
        return True, "Ready to post"
    
    async def post_insight(self, insight: Insight) -> PostResult:
        """
        Post an insight to X with chart image.
        
        Args:
            insight: Insight object
            
        Returns:
            PostResult object
        """
        # Check if should post
        should_post, reason = self.should_post_insight(insight)
        if not should_post:
            logger.info(f"Skipping insight {insight.id}: {reason}")
            return PostResult(
                success=False,
                error=reason,
                insight_id=insight.id
            )
        
        # Compose tweet text
        tweet_text = self.compose_tweet(insight)
        
        # Download and upload chart image if available
        media_ids = []
        if insight.chart_url:
            chart_bytes = await self.api_client.download_chart_image(insight.chart_url)
            if chart_bytes:
                media_id = self.x_client.upload_media(chart_bytes)
                if media_id:
                    media_ids.append(media_id)
                else:
                    logger.warning(f"Failed to upload chart for insight {insight.id}")
            else:
                logger.warning(f"Failed to download chart for insight {insight.id}")
        
        # Post tweet
        tweet_id = self.x_client.post_tweet(
            text=tweet_text,
            media_ids=media_ids if media_ids else None
        )
        
        if tweet_id:
            # Mark as posted in Redis
            self.redis_client.mark_insight_posted(
                insight.id,
                insight.signal_type.value
            )
            
            logger.info(f"Successfully posted insight {insight.id} as tweet {tweet_id}")
            return PostResult(
                success=True,
                tweet_id=tweet_id,
                insight_id=insight.id
            )
        else:
            logger.error(f"Failed to post insight {insight.id}")
            return PostResult(
                success=False,
                error="Failed to post tweet",
                insight_id=insight.id
            )
    
    async def process_hourly_insights(self) -> List[PostResult]:
        """
        Process and post insights from hourly check.
        
        Returns:
            List of PostResult objects
        """
        logger.info("Starting hourly insight processing")
        
        # Fetch publishable insights
        insights = await self.api_client.get_publishable_insights(limit=10)
        
        if not insights:
            logger.info("No publishable insights found")
            return []
        
        # Post each insight
        results = []
        for insight in insights:
            result = await self.post_insight(insight)
            results.append(result)
            
            # Log result
            if result.success:
                logger.info(f"Posted insight {insight.id}: {insight.headline[:50]}...")
            else:
                logger.warning(f"Skipped insight {insight.id}: {result.error}")
        
        # Summary
        successful = sum(1 for r in results if r.success)
        logger.info(f"Hourly processing complete: {successful}/{len(results)} insights posted")
        
        return results
