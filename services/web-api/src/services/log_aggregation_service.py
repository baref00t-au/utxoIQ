"""
Log Aggregation Service

Provides centralized log collection and search across all services using Google Cloud Logging.
"""

from datetime import datetime
from typing import Dict, List, Optional
from google.cloud import logging
from google.cloud.logging_v2 import DESCENDING
import logging as std_logging

logger = std_logging.getLogger(__name__)


class LogAggregationError(Exception):
    """Base exception for log aggregation errors"""
    pass


class LogSearchError(LogAggregationError):
    """Error during log search operation"""
    pass


class LogAggregationService:
    """Service for aggregating and searching logs from Cloud Logging"""
    
    def __init__(self, project_id: str):
        """
        Initialize the log aggregation service.
        
        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.client = logging.Client(project=project_id)
        logger.info(f"LogAggregationService initialized for project: {project_id}")
    
    async def search_logs(
        self,
        query: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None,
        service: Optional[str] = None,
        limit: int = 100,
        page_token: Optional[str] = None
    ) -> Dict:
        """
        Search logs with filters.
        
        Args:
            query: Full-text search query
            start_time: Start of time range
            end_time: End of time range
            severity: Log severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            service: Service name to filter by
            limit: Maximum number of results (1-1000)
            page_token: Token for pagination
            
        Returns:
            Dictionary containing:
                - logs: List of log entries
                - next_page_token: Token for next page (if available)
                - total_count: Approximate total count
                
        Raises:
            LogSearchError: If search operation fails
        """
        try:
            # Build filter string
            filter_parts = []
            
            # Time range filters
            if start_time:
                filter_parts.append(f'timestamp >= "{start_time.isoformat()}Z"')
            if end_time:
                filter_parts.append(f'timestamp <= "{end_time.isoformat()}Z"')
            
            # Severity filter
            if severity:
                severity_upper = severity.upper()
                filter_parts.append(f'severity = "{severity_upper}"')
            
            # Service filter
            if service:
                filter_parts.append(f'resource.labels.service_name = "{service}"')
            
            # Full-text search
            if query:
                # Escape special characters in query
                escaped_query = query.replace('"', '\\"')
                filter_parts.append(f'textPayload =~ "{escaped_query}"')
            
            # Combine filters
            filter_str = " AND ".join(filter_parts) if filter_parts else None
            
            logger.info(f"Searching logs with filter: {filter_str}")
            
            # Validate limit
            if limit < 1 or limit > 1000:
                limit = 100
            
            # Execute search
            entries = self.client.list_entries(
                filter_=filter_str,
                order_by=DESCENDING,
                max_results=limit,
                page_token=page_token
            )
            
            # Format results
            logs = []
            next_token = None
            
            # Iterate through entries
            page = entries.pages.__next__()
            for entry in page:
                logs.append(self._format_log_entry(entry))
            
            # Get next page token if available
            if hasattr(entries, 'next_page_token'):
                next_token = entries.next_page_token
            
            result = {
                "logs": logs,
                "next_page_token": next_token,
                "total_count": len(logs),
                "filter": filter_str
            }
            
            logger.info(f"Found {len(logs)} log entries")
            return result
            
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            raise LogSearchError(f"Failed to search logs: {str(e)}")
    
    async def get_log_context(
        self,
        target_log_id: str,
        target_timestamp: datetime,
        context_lines: int = 10,
        service: Optional[str] = None
    ) -> Dict:
        """
        Get surrounding log entries for context.
        
        Args:
            target_log_id: ID of the target log entry
            target_timestamp: Timestamp of the target log
            context_lines: Number of lines before and after (default: 10)
            service: Optional service name to filter by
            
        Returns:
            Dictionary containing:
                - before: List of log entries before target
                - target: The target log entry
                - after: List of log entries after target
                
        Raises:
            LogSearchError: If context retrieval fails
        """
        try:
            # Get logs before target
            before_filter_parts = [
                f'timestamp < "{target_timestamp.isoformat()}Z"'
            ]
            if service:
                before_filter_parts.append(f'resource.labels.service_name = "{service}"')
            
            before_filter = " AND ".join(before_filter_parts)
            
            before_entries = self.client.list_entries(
                filter_=before_filter,
                order_by=DESCENDING,
                max_results=context_lines
            )
            
            before_logs = []
            for entry in before_entries:
                before_logs.append(self._format_log_entry(entry))
            
            # Reverse to get chronological order
            before_logs.reverse()
            
            # Get logs after target
            after_filter_parts = [
                f'timestamp > "{target_timestamp.isoformat()}Z"'
            ]
            if service:
                after_filter_parts.append(f'resource.labels.service_name = "{service}"')
            
            after_filter = " AND ".join(after_filter_parts)
            
            # For "after" logs, we want ascending order
            after_entries = self.client.list_entries(
                filter_=after_filter,
                order_by=logging.ASCENDING,
                max_results=context_lines
            )
            
            after_logs = []
            for entry in after_entries:
                after_logs.append(self._format_log_entry(entry))
            
            # Try to find the target log
            target_log = None
            target_filter = f'insertId = "{target_log_id}"'
            target_entries = self.client.list_entries(
                filter_=target_filter,
                max_results=1
            )
            
            for entry in target_entries:
                target_log = self._format_log_entry(entry)
                target_log["is_target"] = True
                break
            
            result = {
                "before": before_logs,
                "target": target_log,
                "after": after_logs,
                "context_lines": context_lines
            }
            
            logger.info(
                f"Retrieved log context: {len(before_logs)} before, "
                f"{len(after_logs)} after target"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving log context: {e}")
            raise LogSearchError(f"Failed to retrieve log context: {str(e)}")
    
    def _format_log_entry(self, entry) -> Dict:
        """
        Format a log entry for API response.
        
        Args:
            entry: Cloud Logging entry object
            
        Returns:
            Formatted log entry dictionary
        """
        # Extract basic fields
        formatted = {
            "log_id": entry.insert_id,
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            "severity": entry.severity,
            "message": None,
            "resource": {},
            "labels": {},
            "trace": entry.trace,
            "span_id": entry.span_id,
        }
        
        # Get message from payload
        if hasattr(entry, 'payload') and entry.payload:
            if isinstance(entry.payload, str):
                formatted["message"] = entry.payload
            elif isinstance(entry.payload, dict):
                formatted["message"] = entry.payload.get("message", str(entry.payload))
                formatted["json_payload"] = entry.payload
            else:
                formatted["message"] = str(entry.payload)
        
        # Extract resource information
        if hasattr(entry, 'resource') and entry.resource:
            formatted["resource"] = {
                "type": entry.resource.type if hasattr(entry.resource, 'type') else None,
                "labels": dict(entry.resource.labels) if hasattr(entry.resource, 'labels') else {}
            }
        
        # Extract labels
        if hasattr(entry, 'labels') and entry.labels:
            formatted["labels"] = dict(entry.labels)
        
        # Extract HTTP request info if available
        if hasattr(entry, 'http_request') and entry.http_request:
            formatted["http_request"] = {
                "method": entry.http_request.request_method,
                "url": entry.http_request.request_url,
                "status": entry.http_request.status,
                "user_agent": entry.http_request.user_agent,
            }
        
        return formatted
    
    async def get_log_statistics(
        self,
        start_time: datetime,
        end_time: datetime,
        service: Optional[str] = None
    ) -> Dict:
        """
        Get log statistics for a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            service: Optional service name to filter by
            
        Returns:
            Dictionary containing log statistics
        """
        try:
            filter_parts = [
                f'timestamp >= "{start_time.isoformat()}Z"',
                f'timestamp <= "{end_time.isoformat()}Z"'
            ]
            
            if service:
                filter_parts.append(f'resource.labels.service_name = "{service}"')
            
            filter_str = " AND ".join(filter_parts)
            
            # Count logs by severity
            severity_counts = {
                "DEBUG": 0,
                "INFO": 0,
                "WARNING": 0,
                "ERROR": 0,
                "CRITICAL": 0
            }
            
            # Sample logs to estimate counts (Cloud Logging doesn't provide direct counts)
            entries = self.client.list_entries(
                filter_=filter_str,
                max_results=1000
            )
            
            total_count = 0
            for entry in entries:
                total_count += 1
                severity = entry.severity if hasattr(entry, 'severity') else "INFO"
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            return {
                "total_count": total_count,
                "severity_counts": severity_counts,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "service": service
            }
            
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            raise LogSearchError(f"Failed to get log statistics: {str(e)}")
