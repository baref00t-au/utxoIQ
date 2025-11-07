"""Tests for feedback resource."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from utxoiq import UtxoIQClient
from utxoiq.models import UserFeedback, AccuracyLeaderboard


class TestFeedbackResource:
    """Test cases for FeedbackResource."""
    
    @patch('requests.Session.request')
    def test_submit_feedback(self, mock_request):
        """Test submitting feedback for an insight."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "insight_id": "insight-123",
            "user_id": "user-456",
            "rating": "useful",
            "timestamp": "2025-11-07T10:00:00Z",
            "comment": "Great analysis"
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(firebase_token="test-token")
        feedback = client.feedback.submit(
            insight_id="insight-123",
            rating="useful",
            comment="Great analysis"
        )
        
        assert isinstance(feedback, UserFeedback)
        assert feedback.rating == "useful"
        assert feedback.comment == "Great analysis"
    
    @patch('requests.Session.request')
    def test_get_accuracy_leaderboard(self, mock_request):
        """Test getting accuracy leaderboard."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "leaderboard": [
                {
                    "model_version": "v1.0.0",
                    "accuracy_rating": 0.92,
                    "total_ratings": 1000,
                    "useful_count": 920,
                    "not_useful_count": 80
                }
            ]
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        leaderboard = client.feedback.get_accuracy_leaderboard()
        
        assert len(leaderboard) == 1
        assert isinstance(leaderboard[0], AccuracyLeaderboard)
        assert leaderboard[0].model_version == "v1.0.0"
        assert leaderboard[0].accuracy_rating == 0.92
