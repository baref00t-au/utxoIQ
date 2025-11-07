"""Main client for utxoIQ API."""
import time
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    UtxoIQError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    SubscriptionRequiredError,
    DataUnavailableError,
    ConfidenceTooLowError
)
from .resources.insights import InsightsResource
from .resources.alerts import AlertsResource
from .resources.feedback import FeedbackResource
from .resources.daily_brief import DailyBriefResource
from .resources.chat import ChatResource
from .resources.billing import BillingResource
from .resources.email_preferences import EmailPreferencesResource


class UtxoIQClient:
    """Main client for interacting with utxoIQ API."""
    
    def __init__(
        self,
        firebase_token: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://api.utxoiq.com",
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_factor: float = 2.0
    ):
        """
        Initialize utxoIQ client.
        
        Args:
            firebase_token: Firebase Auth JWT token for authentication
            api_key: API key for programmatic access
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff_factor: Backoff factor for exponential retry
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.firebase_token = firebase_token
        self.api_key = api_key
        
        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "utxoiq-python-sdk/1.0.0"
        })
        
        # Set authentication headers
        if firebase_token:
            self.session.headers["Authorization"] = f"Bearer {firebase_token}"
        elif api_key:
            self.session.headers["X-API-Key"] = api_key
        
        # Initialize resource endpoints
        self.insights = InsightsResource(self)
        self.alerts = AlertsResource(self)
        self.feedback = FeedbackResource(self)
        self.daily_brief = DailyBriefResource(self)
        self.chat = ChatResource(self)
        self.billing = BillingResource(self)
        self.email_preferences = EmailPreferencesResource(self)
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests
        
        Returns:
            Response object
        
        Raises:
            UtxoIQError: On API errors
        """
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            self._handle_error_response(response)
            return response
        except requests.exceptions.Timeout:
            raise UtxoIQError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise UtxoIQError("Connection error")
        except requests.exceptions.RequestException as e:
            raise UtxoIQError(f"Request failed: {str(e)}")
    
    def _handle_error_response(self, response: requests.Response):
        """Handle error responses from API."""
        if response.status_code < 400:
            return
        
        try:
            error_data = response.json()
            error_info = error_data.get("error", {})
            message = error_info.get("message", "Unknown error")
            error_code = error_info.get("code")
            details = error_info.get("details", {})
            request_id = error_data.get("request_id")
        except Exception:
            message = response.text or f"HTTP {response.status_code}"
            error_code = None
            details = {}
            request_id = None
        
        # Map status codes to exception types
        if response.status_code == 401:
            raise AuthenticationError(
                message,
                status_code=response.status_code,
                error_code=error_code,
                details=details,
                request_id=request_id
            )
        elif response.status_code == 429:
            retry_after = details.get("retry_after")
            raise RateLimitError(
                message,
                retry_after=retry_after,
                status_code=response.status_code,
                error_code=error_code,
                details=details,
                request_id=request_id
            )
        elif response.status_code == 400:
            raise ValidationError(
                message,
                status_code=response.status_code,
                error_code=error_code,
                details=details,
                request_id=request_id
            )
        elif response.status_code == 404:
            raise NotFoundError(
                message,
                status_code=response.status_code,
                error_code=error_code,
                details=details,
                request_id=request_id
            )
        elif response.status_code == 402:
            raise SubscriptionRequiredError(
                message,
                status_code=response.status_code,
                error_code=error_code,
                details=details,
                request_id=request_id
            )
        elif response.status_code == 503 and error_code == "DATA_UNAVAILABLE":
            raise DataUnavailableError(
                message,
                status_code=response.status_code,
                error_code=error_code,
                details=details,
                request_id=request_id
            )
        elif response.status_code == 422 and error_code == "CONFIDENCE_TOO_LOW":
            raise ConfidenceTooLowError(
                message,
                status_code=response.status_code,
                error_code=error_code,
                details=details,
                request_id=request_id
            )
        else:
            raise UtxoIQError(
                message,
                status_code=response.status_code,
                error_code=error_code,
                details=details,
                request_id=request_id
            )
    
    def get(self, endpoint: str, **kwargs):
        """Make GET request."""
        return self._request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs):
        """Make POST request."""
        return self._request("POST", endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs):
        """Make PUT request."""
        return self._request("PUT", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs):
        """Make DELETE request."""
        return self._request("DELETE", endpoint, **kwargs)
