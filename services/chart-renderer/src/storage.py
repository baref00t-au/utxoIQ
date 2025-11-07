"""
Google Cloud Storage utilities for chart uploads
"""

from google.cloud import storage
from datetime import timedelta
import hashlib
import logging
from typing import Tuple
from .config import settings

logger = logging.getLogger(__name__)


class ChartStorage:
    """Handle chart uploads to Google Cloud Storage"""
    
    def __init__(self):
        """Initialize GCS client"""
        try:
            self.client = storage.Client(project=settings.gcs_project_id)
            self.bucket = self.client.bucket(settings.gcs_bucket_name)
        except Exception as e:
            logger.warning(f"Failed to initialize GCS client: {e}")
            self.client = None
            self.bucket = None
    
    def generate_chart_path(self, signal_type: str, data_hash: str) -> str:
        """
        Generate unique chart path based on signal type and data hash
        
        Args:
            signal_type: Type of signal (mempool, exchange, etc.)
            data_hash: Hash of chart data for uniqueness
            
        Returns:
            GCS path for the chart
        """
        return f"charts/{signal_type}/{data_hash}.png"
    
    def hash_data(self, data: bytes) -> str:
        """
        Generate hash of chart data for unique identification
        
        Args:
            data: Chart image bytes
            
        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(data).hexdigest()[:16]
    
    def upload_chart(self, chart_data: bytes, signal_type: str) -> Tuple[str, str, int]:
        """
        Upload chart to GCS and return signed URL
        
        Args:
            chart_data: PNG image bytes
            signal_type: Type of signal for path organization
            
        Returns:
            Tuple of (signed_url, gcs_path, size_bytes)
        """
        if not self.bucket:
            # Fallback for local development without GCS
            logger.warning("GCS not configured, returning mock URL")
            data_hash = self.hash_data(chart_data)
            mock_path = self.generate_chart_path(signal_type, data_hash)
            return (
                f"http://localhost:8080/mock/{mock_path}",
                mock_path,
                len(chart_data)
            )
        
        try:
            # Generate unique path
            data_hash = self.hash_data(chart_data)
            chart_path = self.generate_chart_path(signal_type, data_hash)
            
            # Upload to GCS
            blob = self.bucket.blob(chart_path)
            blob.upload_from_string(
                chart_data,
                content_type='image/png',
                timeout=30
            )
            
            # Set cache control for CDN
            blob.cache_control = 'public, max-age=3600'
            blob.patch()
            
            # Generate signed URL (valid for 7 days)
            signed_url = blob.generate_signed_url(
                version='v4',
                expiration=timedelta(days=7),
                method='GET'
            )
            
            logger.info(f"Uploaded chart to {chart_path}")
            
            return signed_url, chart_path, len(chart_data)
            
        except Exception as e:
            logger.error(f"Failed to upload chart to GCS: {e}")
            raise
    
    def delete_chart(self, chart_path: str) -> bool:
        """
        Delete chart from GCS
        
        Args:
            chart_path: GCS path to the chart
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bucket:
            return False
        
        try:
            blob = self.bucket.blob(chart_path)
            blob.delete()
            logger.info(f"Deleted chart from {chart_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete chart from GCS: {e}")
            return False


# Global storage instance
chart_storage = ChartStorage()
