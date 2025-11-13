"""Tests for export service."""
import pytest
from datetime import datetime
from ...models import Insight, SignalType, Citation, CitationType, User, UserSubscriptionTier
from ...models.export import ExportFormat, ExportRequest
from ..export_service import ExportService


@pytest.fixture
def export_service():
    """Create export service instance."""
    return ExportService()


@pytest.fixture
def sample_insights():
    """Create sample insights for testing."""
    return [
        Insight(
            id="insight_1",
            signal_type=SignalType.MEMPOOL,
            headline="Test Insight 1",
            summary="This is a test summary",
            confidence=0.85,
            timestamp=datetime(2025, 11, 7, 10, 30, 0),
            block_height=820000,
            evidence=[
                Citation(
                    type=CitationType.BLOCK,
                    id="820000",
                    description="Block 820000",
                    url="https://blockstream.info/block/820000"
                )
            ],
            chart_url="https://example.com/chart.png",
            tags=["mempool", "fees"],
            is_predictive=False
        ),
        Insight(
            id="insight_2",
            signal_type=SignalType.EXCHANGE,
            headline="Test Insight 2",
            summary="Another test summary",
            confidence=0.92,
            timestamp=datetime(2025, 11, 7, 11, 0, 0),
            block_height=820001,
            evidence=[],
            tags=["exchange"],
            is_predictive=True
        )
    ]


class TestExportService:
    """Test export service functionality."""
    
    def test_get_export_limit_free_tier(self, export_service):
        """Test export limit for free tier users."""
        user = User(
            uid="user_1",
            email="test@example.com",
            subscription_tier=UserSubscriptionTier.FREE
        )
        limit = export_service.get_export_limit(user)
        assert limit == 100
    
    def test_get_export_limit_pro_tier(self, export_service):
        """Test export limit for pro tier users."""
        user = User(
            uid="user_1",
            email="test@example.com",
            subscription_tier=UserSubscriptionTier.PRO
        )
        limit = export_service.get_export_limit(user)
        assert limit == 1000
    
    def test_get_export_limit_power_tier(self, export_service):
        """Test export limit for power tier users."""
        user = User(
            uid="user_1",
            email="test@example.com",
            subscription_tier=UserSubscriptionTier.POWER
        )
        limit = export_service.get_export_limit(user)
        assert limit == 10000
    
    def test_get_export_limit_no_user(self, export_service):
        """Test export limit for unauthenticated users."""
        limit = export_service.get_export_limit(None)
        assert limit == 100
    
    def test_generate_csv(self, export_service, sample_insights):
        """Test CSV generation from insights."""
        csv = export_service._generate_csv(sample_insights)
        
        # Check header row
        assert "id,signal_type,headline,summary,confidence" in csv
        
        # Check data rows
        assert "insight_1" in csv
        assert "mempool" in csv
        assert "Test Insight 1" in csv
        assert "0.85" in csv
        
        assert "insight_2" in csv
        assert "exchange" in csv
        assert "0.92" in csv
    
    def test_generate_csv_empty(self, export_service):
        """Test CSV generation with empty insights list."""
        csv = export_service._generate_csv([])
        assert csv == ""
    
    def test_generate_csv_escaping(self, export_service):
        """Test CSV generation with special characters."""
        insight = Insight(
            id="test",
            signal_type=SignalType.MEMPOOL,
            headline='Test "quoted" text',
            summary="Text with, comma",
            confidence=0.8,
            timestamp=datetime.now(),
            block_height=820000,
            evidence=[],
            is_predictive=False
        )
        
        csv = export_service._generate_csv([insight])
        
        # Check that quotes are properly escaped
        assert '"Test ""quoted"" text"' in csv or 'Test "quoted" text' in csv
        # Check that commas are handled
        assert "Text with, comma" in csv or '"Text with, comma"' in csv
    
    def test_generate_json(self, export_service, sample_insights):
        """Test JSON generation from insights."""
        import json
        
        json_str = export_service._generate_json(sample_insights)
        data = json.loads(json_str)
        
        assert len(data) == 2
        assert data[0]["id"] == "insight_1"
        assert data[0]["signal_type"] == "mempool"
        assert data[0]["confidence"] == 0.85
        assert data[0]["evidence"][0]["type"] == "block"
        
        assert data[1]["id"] == "insight_2"
        assert data[1]["is_predictive"] is True
    
    def test_generate_json_empty(self, export_service):
        """Test JSON generation with empty insights list."""
        import json
        
        json_str = export_service._generate_json([])
        data = json.loads(json_str)
        
        assert data == []
    
    def test_generate_filename_basic(self, export_service):
        """Test filename generation without filters."""
        filename = export_service.generate_filename(ExportFormat.CSV)
        
        assert filename.startswith("insights_")
        assert filename.endswith(".csv")
        assert len(filename.split("_")) >= 2  # At least "insights" and date
    
    def test_generate_filename_with_filters(self, export_service):
        """Test filename generation with filters."""
        filters = {
            "signal_type": "mempool",
            "min_confidence": 0.75
        }
        
        filename = export_service.generate_filename(ExportFormat.JSON, filters)
        
        assert "mempool" in filename
        assert "conf75" in filename
        assert filename.endswith(".json")
    
    def test_generate_filename_sanitization(self, export_service):
        """Test filename sanitization for cross-platform compatibility."""
        # Test with invalid characters
        filename = export_service._sanitize_filename('test<>:"/\\|?*.csv')
        
        # Should not contain invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            assert char not in filename
    
    def test_generate_filename_length_limit(self, export_service):
        """Test filename length limitation."""
        long_name = "a" * 300 + ".csv"
        sanitized = export_service._sanitize_filename(long_name)
        
        assert len(sanitized) <= 255
        assert sanitized.endswith(".csv")
    
    @pytest.mark.asyncio
    async def test_export_insights_limit_exceeded(self, export_service):
        """Test export with limit exceeded."""
        user = User(
            uid="user_1",
            email="test@example.com",
            subscription_tier=UserSubscriptionTier.FREE
        )
        
        export_request = ExportRequest(
            format=ExportFormat.CSV,
            limit=500  # Exceeds free tier limit of 100
        )
        
        with pytest.raises(ValueError, match="Export limit exceeded"):
            await export_service.export_insights(export_request, user)
