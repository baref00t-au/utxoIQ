"""Data models for the Web API service."""
from .insights import Insight, InsightResponse, InsightListResponse
from .alerts import Alert, AlertCreate, AlertUpdate, AlertResponse
from .feedback import UserFeedback, FeedbackCreate, FeedbackResponse
from .errors import ErrorCode, ErrorDetail, ErrorResponse
from .auth import User, UserSubscriptionTier
from .daily_brief import DailyBrief, DailyBriefResponse
from .chat import ChatQuery, ChatResponse
from .billing import SubscriptionInfo, SubscriptionResponse
from .email_preferences import EmailPreferences, EmailPreferencesUpdate

__all__ = [
    "Insight",
    "InsightResponse",
    "InsightListResponse",
    "Alert",
    "AlertCreate",
    "AlertUpdate",
    "AlertResponse",
    "UserFeedback",
    "FeedbackCreate",
    "FeedbackResponse",
    "ErrorCode",
    "ErrorDetail",
    "ErrorResponse",
    "User",
    "UserSubscriptionTier",
    "DailyBrief",
    "DailyBriefResponse",
    "ChatQuery",
    "ChatResponse",
    "SubscriptionInfo",
    "SubscriptionResponse",
    "EmailPreferences",
    "EmailPreferencesUpdate",
]
