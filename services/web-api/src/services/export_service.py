"""Export service for data export functionality."""
import logging
import csv
import json
from io import StringIO
from typing import List, Optional, Tuple
from datetime import datetime
from ..models import Insight, User, SignalType, UserSubscriptionTier
from ..models.export import ExportFormat, ExportRequest
from .insights_service import InsightsService

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting insights data."""
    
    # Subscription tier limits for export
    TIER_LIMITS = {
        UserSubscriptionTier.FREE: 100,
        UserSubscriptionTier.PRO: 1000,
        UserSubscriptionTier.POWER: 10000,
        UserSubscriptionTier.WHITE_LABEL: 10000
    }
    
    def __init__(self):
        self.insights_service = InsightsService()
    
    def get_export_limit(self, user: Optional[User]) -> int:
        """
        Get export limit based on user subscription tier.
        
        Args:
            user: Optional authenticated user
            
        Returns:
            Maximum number of records allowed for export
        """
        if not user:
            return self.TIER_LIMITS[UserSubscriptionTier.FREE]
        
        tier = user.subscription_tier
        return self.TIER_LIMITS.get(tier, self.TIER_LIMITS[UserSubscriptionTier.FREE])
    
    async def export_insights(
        self,
        export_request: ExportRequest,
        user: Optional[User] = None
    ) -> Tuple[str, str, int]:
        """
        Export insights data in the requested format.
        
        Args:
            export_request: Export request with format and filters
            user: Optional authenticated user
            
        Returns:
            Tuple of (content, content_type, record_count)
            
        Raises:
            ValueError: If export limit exceeded
        """
        # Check export limit
        max_limit = self.get_export_limit(user)
        if export_request.limit > max_limit:
            raise ValueError(
                f"Export limit exceeded. Your tier allows up to {max_limit} records."
            )
        
        # Extract filters
        filters = export_request.filters or {}
        signal_type = None
        min_confidence = None
        
        if "signal_type" in filters:
            try:
                signal_type = SignalType(filters["signal_type"])
            except ValueError:
                pass
        
        if "min_confidence" in filters:
            min_confidence = filters.get("min_confidence")
        
        # Fetch insights
        insights, total = await self.insights_service.get_latest_insights(
            limit=export_request.limit,
            page=1,
            signal_type=signal_type,
            min_confidence=min_confidence,
            user=user
        )
        
        # Generate export content
        if export_request.format == ExportFormat.CSV:
            content = self._generate_csv(insights)
            content_type = "text/csv"
        else:  # JSON
            content = self._generate_json(insights)
            content_type = "application/json"
        
        return content, content_type, len(insights)
    
    def _generate_csv(self, insights: List[Insight]) -> str:
        """
        Generate CSV content from insights.
        
        Args:
            insights: List of insights to export
            
        Returns:
            CSV content as string
        """
        if not insights:
            return ""
        
        output = StringIO()
        
        # Define CSV columns
        fieldnames = [
            "id",
            "signal_type",
            "headline",
            "summary",
            "confidence",
            "timestamp",
            "block_height",
            "chart_url",
            "tags",
            "accuracy_rating",
            "is_predictive"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        
        for insight in insights:
            row = {
                "id": insight.id,
                "signal_type": insight.signal_type.value,
                "headline": insight.headline,
                "summary": insight.summary,
                "confidence": insight.confidence,
                "timestamp": insight.timestamp.isoformat(),
                "block_height": insight.block_height,
                "chart_url": insight.chart_url or "",
                "tags": ",".join(insight.tags) if insight.tags else "",
                "accuracy_rating": insight.accuracy_rating or "",
                "is_predictive": insight.is_predictive
            }
            writer.writerow(row)
        
        return output.getvalue()
    
    def _generate_json(self, insights: List[Insight]) -> str:
        """
        Generate JSON content from insights.
        
        Args:
            insights: List of insights to export
            
        Returns:
            JSON content as string
        """
        # Convert insights to dict format
        data = []
        for insight in insights:
            insight_dict = {
                "id": insight.id,
                "signal_type": insight.signal_type.value,
                "headline": insight.headline,
                "summary": insight.summary,
                "confidence": insight.confidence,
                "timestamp": insight.timestamp.isoformat(),
                "block_height": insight.block_height,
                "evidence": [
                    {
                        "type": citation.type.value,
                        "id": citation.id,
                        "description": citation.description,
                        "url": citation.url
                    }
                    for citation in insight.evidence
                ],
                "chart_url": insight.chart_url,
                "tags": insight.tags,
                "accuracy_rating": insight.accuracy_rating,
                "is_predictive": insight.is_predictive
            }
            
            # Include explainability if present
            if insight.explainability:
                insight_dict["explainability"] = {
                    "confidence_factors": insight.explainability.confidence_factors,
                    "explanation": insight.explainability.explanation,
                    "supporting_evidence": insight.explainability.supporting_evidence
                }
            
            data.append(insight_dict)
        
        return json.dumps(data, indent=2)
    
    def generate_filename(
        self,
        export_format: ExportFormat,
        filters: Optional[dict] = None
    ) -> str:
        """
        Generate export filename based on filters and timestamp.
        
        Args:
            export_format: Export format (CSV or JSON)
            filters: Optional filter criteria
            
        Returns:
            Sanitized filename
        """
        # Start with base name
        parts = ["insights"]
        
        # Add filter criteria
        if filters:
            if "signal_type" in filters:
                parts.append(filters["signal_type"])
            
            if "min_confidence" in filters:
                conf = filters["min_confidence"]
                parts.append(f"conf{int(conf * 100)}")
        
        # Add timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d")
        parts.append(timestamp)
        
        # Join parts and add extension
        filename = "_".join(parts)
        extension = "csv" if export_format == ExportFormat.CSV else "json"
        
        # Sanitize filename for cross-platform compatibility
        filename = self._sanitize_filename(f"{filename}.{extension}")
        
        return filename
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for cross-platform compatibility.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(". ")
        
        # Limit length
        max_length = 255
        if len(filename) > max_length:
            name, ext = filename.rsplit(".", 1)
            name = name[:max_length - len(ext) - 1]
            filename = f"{name}.{ext}"
        
        return filename
