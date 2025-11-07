"""Tests for alerts resource."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from utxoiq import UtxoIQClient
from utxoiq.models import Alert


class TestAlertsResource:
    """Test cases for AlertsResource."""
    
    @patch('requests.Session.request')
    def test_list_alerts(self, mock_request):
        """Test listing user alerts."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "alerts": [
                {
                    "id": "alert-1",
                    "user_id": "user-123",
                    "signal_type": "mempool",
                    "threshold": 100.0,
                    "operator": "gt",
                    "is_active": True,
                    "created_at": "2025-11-07T10:00:00Z"
                }
            ]
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(firebase_token="test-token")
        alerts = client.alerts.list()
        
        assert len(alerts) == 1
        assert isinstance(alerts[0], Alert)
        assert alerts[0].signal_type == "mempool"
    
    @patch('requests.Session.request')
    def test_create_alert(self, mock_request):
        """Test creating a new alert."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "alert-new",
            "user_id": "user-123",
            "signal_type": "exchange",
            "threshold": 1000.0,
            "operator": "gt",
            "is_active": True,
            "created_at": "2025-11-07T10:00:00Z",
            "notification_channel": "email"
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(firebase_token="test-token")
        alert = client.alerts.create(
            signal_type="exchange",
            threshold=1000.0,
            operator="gt"
        )
        
        assert isinstance(alert, Alert)
        assert alert.signal_type == "exchange"
        assert alert.threshold == 1000.0
    
    @patch('requests.Session.request')
    def test_update_alert(self, mock_request):
        """Test updating an alert."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "alert-1",
            "user_id": "user-123",
            "signal_type": "mempool",
            "threshold": 150.0,
            "operator": "gt",
            "is_active": False,
            "created_at": "2025-11-07T10:00:00Z"
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(firebase_token="test-token")
        alert = client.alerts.update("alert-1", threshold=150.0, is_active=False)
        
        assert alert.threshold == 150.0
        assert alert.is_active is False
    
    @patch('requests.Session.request')
    def test_delete_alert(self, mock_request):
        """Test deleting an alert."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(firebase_token="test-token")
        result = client.alerts.delete("alert-1")
        
        assert result is True
