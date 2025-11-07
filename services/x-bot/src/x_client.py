"""X API client wrapper."""
import tweepy
import logging
from typing import Optional, List
from .config import settings

logger = logging.getLogger(__name__)


class XClient:
    """Wrapper for X API v2 interactions."""
    
    def __init__(self):
        """Initialize X API client."""
        # OAuth 1.0a for posting
        self.auth = tweepy.OAuth1UserHandler(
            settings.x_api_key,
            settings.x_api_secret,
            settings.x_access_token,
            settings.x_access_token_secret
        )
        
        # API v2 client
        self.client = tweepy.Client(
            bearer_token=settings.x_bearer_token,
            consumer_key=settings.x_api_key,
            consumer_secret=settings.x_api_secret,
            access_token=settings.x_access_token,
            access_token_secret=settings.x_access_token_secret,
            wait_on_rate_limit=True
        )
        
        # API v1.1 for media upload
        self.api = tweepy.API(self.auth)
        
        logger.info("X API client initialized")
    
    def upload_media(self, image_bytes: bytes) -> Optional[str]:
        """
        Upload media to X and return media ID.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Media ID string or None if upload fails
        """
        try:
            media = self.api.media_upload(
                filename="chart.png",
                file=image_bytes
            )
            logger.info(f"Media uploaded successfully: {media.media_id_string}")
            return media.media_id_string
        except Exception as e:
            logger.error(f"Failed to upload media: {e}")
            return None
    
    def post_tweet(
        self,
        text: str,
        media_ids: Optional[List[str]] = None,
        in_reply_to_tweet_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Post a tweet with optional media and reply context.
        
        Args:
            text: Tweet text (max 280 characters)
            media_ids: List of media IDs to attach
            in_reply_to_tweet_id: Tweet ID to reply to (for threads)
            
        Returns:
            Tweet ID string or None if posting fails
        """
        try:
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids,
                in_reply_to_tweet_id=in_reply_to_tweet_id
            )
            
            tweet_id = response.data['id']
            logger.info(f"Tweet posted successfully: {tweet_id}")
            return tweet_id
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return None
    
    def post_thread(self, tweets: List[str], media_ids_list: Optional[List[List[str]]] = None) -> List[Optional[str]]:
        """
        Post a thread of connected tweets.
        
        Args:
            tweets: List of tweet texts
            media_ids_list: Optional list of media IDs for each tweet
            
        Returns:
            List of tweet IDs (None for failed tweets)
        """
        tweet_ids = []
        previous_tweet_id = None
        
        if media_ids_list is None:
            media_ids_list = [None] * len(tweets)
        
        for i, (text, media_ids) in enumerate(zip(tweets, media_ids_list)):
            tweet_id = self.post_tweet(
                text=text,
                media_ids=media_ids,
                in_reply_to_tweet_id=previous_tweet_id
            )
            tweet_ids.append(tweet_id)
            
            if tweet_id:
                previous_tweet_id = tweet_id
            else:
                logger.error(f"Failed to post tweet {i+1} in thread")
                break
        
        return tweet_ids
