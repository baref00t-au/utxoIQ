"""
Tests for GCS storage utilities
"""

import pytest
from src.storage import ChartStorage


class TestChartStorage:
    """Tests for chart storage functionality"""
    
    def test_generate_chart_path(self):
        """Test chart path generation"""
        storage = ChartStorage()
        
        path = storage.generate_chart_path("mempool", "abc123")
        assert path == "charts/mempool/abc123.png"
        
        path = storage.generate_chart_path("exchange", "def456")
        assert path == "charts/exchange/def456.png"
    
    def test_hash_data(self):
        """Test data hashing for uniqueness"""
        storage = ChartStorage()
        
        data1 = b"test data 1"
        data2 = b"test data 2"
        
        hash1 = storage.hash_data(data1)
        hash2 = storage.hash_data(data2)
        
        # Hashes should be different
        assert hash1 != hash2
        
        # Same data should produce same hash
        hash1_again = storage.hash_data(data1)
        assert hash1 == hash1_again
        
        # Hash should be 16 characters
        assert len(hash1) == 16
    
    def test_upload_chart_without_gcs(self):
        """Test chart upload fallback when GCS not configured"""
        storage = ChartStorage()
        
        # Mock chart data
        chart_data = b"fake png data"
        
        # Should return mock URL when GCS not configured
        url, path, size = storage.upload_chart(chart_data, "mempool")
        
        assert "mock" in url or url.startswith("http")
        assert "mempool" in path
        assert size == len(chart_data)
