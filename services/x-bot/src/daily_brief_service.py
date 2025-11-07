"""Service for generating and posting daily Bitcoin Pulse threads."""
import logging
from typing import List, Optional
from datetime import date, datetime
from .models import DailyBrief, Insight
from .x_client import XClient
from .redis_client import RedisClient
from .api_client import APIClient
from .config import settings

logger = logging.getLogger(__name__)


class DailyBriefService:
    """Service for managing daily Bitcoin Pulse threads."""
    
    def __init__(self):
        """Initialize daily brief service."""
        self.x_client = XClient()
        self.redis_client = RedisClient()
        self.api_client = APIClient()
        logger.info("Daily brief service initialized")
    
    def compose_thread_intro(self, brief: DailyBrief) -> str:
        """
        Compose the intro tweet for the daily thread.
        
        Args:
            brief: DailyBrief object
            
        Returns:
            Tweet text for thread intro
        """
        # Parse date for display
        brief_date = datetime.fromisoformat(brief.date)
        date_str = brief_date.strftime("%B %d, %Y")
        
        intro = f"⚡ Bitcoin Pulse — {date_str}\n\n"
        intro += f"Top {len(brief.top_insights)} blockchain events from the past 24 hours:\n\n"
        intro += "🧵 Thread below 👇"
        
        return intro
    
    def compose_insight_tweet(self, insight: Insight, index: int) -> str:
        """
        Compose a tweet for a single insight in the thread.
        
        Args:
            insight: Insight object
            index: Position in the thread (1-indexed)
            
        Returns:
            Tweet text
        """
        # Signal type emoji mapping
        emoji_map = {
            "mempool": "📊",
            "exchange": "🏦",
            "miner": "⛏️",
            "whale": "🐋"
        }
        
        emoji = emoji_map.get(insight.signal_type.value, "📈")
        confidence_pct = int(insight.confidence * 100)
        
        tweet = f"{index}/ {emoji} {insight.signal_type.value.upper()}\n\n"
        tweet += f"{insight.headline}\n\n"
        
        # Add summary if it fits
        max_summary_length = 280 - len(tweet) - 50  # Reserve space for metadata
        if len(insight.summary) <= max_summary_length:
            tweet += f"{insight.summary}\n\n"
        else:
            # Truncate summary
            tweet += f"{insight.summary[:max_summary_length-3]}...\n\n"
        
        tweet += f"Confidence: {confidence_pct}% | Block: {insight.block_height}"
        
        # Ensure it fits in 280 characters
        if len(tweet) > 280:
            # Simplify if too long
            tweet = f"{index}/ {emoji} {insight.signal_type.value.upper()}\n\n"
            tweet += f"{insight.headline}\n\n"
            tweet += f"Confidence: {confidence_pct}% | Block: {insight.block_height}"
        
        return tweet
    
    def compose_thread_outro(self) -> str:
        """
        Compose the outro tweet for the daily thread.
        
        Returns:
            Tweet text for thread outro
        """
        outro = "📱 Get real-time Bitcoin intelligence:\n"
        outro += "→ utxoiq.com\n\n"
        outro += "🔔 Never miss an insight — follow us for hourly updates!"
        
        return outro
    
    async def should_post_daily_brief(self, brief_date: date) -> tuple[bool, str]:
        """
        Determine if daily brief should be posted.
        
        Args:
            brief_date: Date of the brief
            
        Returns:
            Tuple of (should_post, reason)
        """
        date_str = brief_date.isoformat()
        
        # Check if already posted today
        last_posted = self.redis_client.get_last_daily_brief_date()
        if last_posted == date_str:
            return False, f"Daily brief for {date_str} already posted"
        
        # Check if brief is available
        brief = await self.api_client.get_daily_brief(brief_date)
        if not brief:
            return False, f"Daily brief for {date_str} not available"
        
        if not brief.top_insights:
            return False, f"Daily brief for {date_str} has no insights"
        
        return True, "Ready to post"
    
    async def post_daily_brief(self, brief_date: Optional[date] = None) -> List[Optional[str]]:
        """
        Post the daily Bitcoin Pulse thread.
        
        Args:
            brief_date: Date for the brief (default: today)
            
        Returns:
            List of tweet IDs (None for failed tweets)
        """
        if brief_date is None:
            brief_date = date.today()
        
        date_str = brief_date.isoformat()
        
        logger.info(f"Starting daily brief posting for {date_str}")
        
        # Check if should post
        should_post, reason = await self.should_post_daily_brief(brief_date)
        if not should_post:
            logger.info(f"Skipping daily brief: {reason}")
            return []
        
        # Fetch brief
        brief = await self.api_client.get_daily_brief(brief_date)
        if not brief:
            logger.error(f"Failed to fetch daily brief for {date_str}")
            return []
        
        # Compose thread tweets
        tweets = []
        
        # 1. Intro tweet
        tweets.append(self.compose_thread_intro(brief))
        
        # 2. Insight tweets (one per insight)
        for i, insight in enumerate(brief.top_insights, start=1):
            tweets.append(self.compose_insight_tweet(insight, i))
        
        # 3. Outro tweet
        tweets.append(self.compose_thread_outro())
        
        logger.info(f"Composed thread with {len(tweets)} tweets")
        
        # Post thread
        tweet_ids = self.x_client.post_thread(tweets)
        
        # Check success
        successful_tweets = sum(1 for tid in tweet_ids if tid is not None)
        
        if successful_tweets > 0:
            # Mark as posted
            self.redis_client.set_last_daily_brief_date(date_str)
            logger.info(f"Successfully posted daily brief thread: {successful_tweets}/{len(tweets)} tweets")
        else:
            logger.error("Failed to post any tweets in daily brief thread")
        
        return tweet_ids
    
    async def check_and_post_daily_brief(self) -> List[Optional[str]]:
        """
        Check if it's time to post daily brief and post if needed.
        
        Returns:
            List of tweet IDs or empty list if not time to post
        """
        now = datetime.utcnow()
        target_time = settings.daily_brief_time  # e.g., "07:00"
        
        # Parse target time
        target_hour, target_minute = map(int, target_time.split(":"))
        
        # Check if current time matches target (within 5-minute window)
        if now.hour == target_hour and abs(now.minute - target_minute) <= 5:
            logger.info(f"Daily brief time reached: {now.strftime('%H:%M')} UTC")
            return await self.post_daily_brief()
        else:
            logger.debug(f"Not time for daily brief yet: {now.strftime('%H:%M')} UTC")
            return []
