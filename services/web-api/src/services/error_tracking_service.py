"""
Error Tracking Service

Integrates with Google Cloud Error Reporting to capture, group, and track errors.
Provides error analytics including frequency, affected users, and code commit linking.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from google.cloud import errorreporting_v1beta1
from google.cloud.errorreporting_v1beta1 import ErrorStatsServiceClient, ErrorGroupServiceClient
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)


class ErrorTrackingService:
    """Service for error tracking and reporting using Cloud Error Reporting"""
    
    def __init__(self, project_id: str):
        """
        Initialize error tracking service.
        
        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.project_name = f"projects/{project_id}"
        self.error_stats_client = ErrorStatsServiceClient()
        self.error_group_client = ErrorGroupServiceClient()
        logger.info(f"Initialized ErrorTrackingService for project {project_id}")
    
    async def list_error_groups(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page_size: int = 100,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List error groups with filtering.
        
        Args:
            service: Filter by service name (optional)
            start_time: Start of time range (optional, defaults to 24h ago)
            end_time: End of time range (optional, defaults to now)
            page_size: Number of results per page
            page_token: Token for pagination
        
        Returns:
            Dictionary containing:
            - error_groups: List of error group data
            - next_page_token: Token for next page (if available)
            - total_count: Total number of error groups
        
        Raises:
            GoogleAPIError: If API call fails
        """
        try:
            # Default time range to last 24 hours
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Build time range
            time_range = errorreporting_v1beta1.QueryTimeRange(
                period=errorreporting_v1beta1.QueryTimeRange.Period.PERIOD_1_HOUR
            )
            
            # Build service filter if specified
            service_filter = None
            if service:
                service_filter = errorreporting_v1beta1.ServiceContextFilter(
                    service=service
                )
            
            # List error group stats
            request = errorreporting_v1beta1.ListGroupStatsRequest(
                project_name=self.project_name,
                time_range=time_range,
                service_filter=service_filter,
                page_size=page_size,
                page_token=page_token or ""
            )
            
            response = self.error_stats_client.list_group_stats(request=request)
            
            error_groups = []
            for group_stat in response:
                # Get error group details
                group_name = group_stat.group.name
                
                # Extract error information
                error_data = {
                    "group_id": group_stat.group.group_id,
                    "group_name": group_name,
                    "count": group_stat.count,
                    "affected_users_count": group_stat.affected_users_count,
                    "first_seen_time": group_stat.first_seen_time.isoformat() if group_stat.first_seen_time else None,
                    "last_seen_time": group_stat.last_seen_time.isoformat() if group_stat.last_seen_time else None,
                    "representative": self._format_error_event(group_stat.representative) if group_stat.representative else None,
                    "num_affected_services": group_stat.num_affected_services,
                    "service_contexts": [
                        {
                            "service": ctx.service,
                            "version": ctx.version
                        }
                        for ctx in group_stat.affected_services
                    ] if group_stat.affected_services else []
                }
                
                error_groups.append(error_data)
            
            logger.info(
                f"Listed {len(error_groups)} error groups "
                f"(service={service}, period={start_time} to {end_time})"
            )
            
            return {
                "error_groups": error_groups,
                "next_page_token": response.next_page_token if hasattr(response, 'next_page_token') else None,
                "total_count": len(error_groups)
            }
        
        except GoogleAPIError as e:
            logger.error(f"Error listing error groups: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing error groups: {e}")
            raise
    
    async def get_error_group(self, group_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific error group.
        
        Args:
            group_id: Error group ID
        
        Returns:
            Dictionary containing error group details
        
        Raises:
            GoogleAPIError: If API call fails
        """
        try:
            group_name = f"{self.project_name}/groups/{group_id}"
            
            request = errorreporting_v1beta1.GetGroupRequest(
                group_name=group_name
            )
            
            group = self.error_group_client.get_group(request=request)
            
            # Get error events for this group
            events = await self.list_error_events(group_id=group_id, page_size=10)
            
            error_data = {
                "group_id": group.group_id,
                "name": group.name,
                "tracking_issues": [
                    {
                        "url": issue.url
                    }
                    for issue in group.tracking_issues
                ] if group.tracking_issues else [],
                "recent_events": events["error_events"]
            }
            
            logger.info(f"Retrieved error group {group_id}")
            
            return error_data
        
        except GoogleAPIError as e:
            logger.error(f"Error retrieving error group {group_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving error group {group_id}: {e}")
            raise
    
    async def list_error_events(
        self,
        group_id: str,
        page_size: int = 100,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List error events for a specific error group.
        
        Args:
            group_id: Error group ID
            page_size: Number of results per page
            page_token: Token for pagination
        
        Returns:
            Dictionary containing:
            - error_events: List of error event data
            - next_page_token: Token for next page (if available)
        
        Raises:
            GoogleAPIError: If API call fails
        """
        try:
            group_name = f"{self.project_name}/groups/{group_id}"
            
            request = errorreporting_v1beta1.ListEventsRequest(
                project_name=self.project_name,
                group_id=group_id,
                page_size=page_size,
                page_token=page_token or ""
            )
            
            response = self.error_stats_client.list_events(request=request)
            
            error_events = []
            for event in response:
                error_events.append(self._format_error_event(event))
            
            logger.debug(f"Listed {len(error_events)} error events for group {group_id}")
            
            return {
                "error_events": error_events,
                "next_page_token": response.next_page_token if hasattr(response, 'next_page_token') else None
            }
        
        except GoogleAPIError as e:
            logger.error(f"Error listing error events for group {group_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing error events for group {group_id}: {e}")
            raise
    
    async def get_error_statistics(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get error statistics and trends.
        
        Args:
            service: Filter by service name (optional)
            start_time: Start of time range (optional, defaults to 7 days ago)
            end_time: End of time range (optional, defaults to now)
        
        Returns:
            Dictionary containing error statistics:
            - total_errors: Total error count
            - unique_error_groups: Number of unique error groups
            - affected_users: Total affected users
            - error_rate_trend: Error rate over time
            - top_errors: Most frequent errors
        
        Raises:
            GoogleAPIError: If API call fails
        """
        try:
            # Default time range to last 7 days
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(days=7)
            
            # Get error groups
            error_groups_data = await self.list_error_groups(
                service=service,
                start_time=start_time,
                end_time=end_time,
                page_size=1000
            )
            
            error_groups = error_groups_data["error_groups"]
            
            # Calculate statistics
            total_errors = sum(group["count"] for group in error_groups)
            unique_error_groups = len(error_groups)
            affected_users = sum(group["affected_users_count"] for group in error_groups)
            
            # Sort by count to get top errors
            top_errors = sorted(
                error_groups,
                key=lambda x: x["count"],
                reverse=True
            )[:10]
            
            # Calculate error rate trend (simplified - would need time series data for accurate trend)
            error_rate_trend = "stable"  # TODO: Implement actual trend calculation
            
            statistics = {
                "period_start": start_time.isoformat(),
                "period_end": end_time.isoformat(),
                "total_errors": total_errors,
                "unique_error_groups": unique_error_groups,
                "affected_users": affected_users,
                "error_rate_trend": error_rate_trend,
                "top_errors": top_errors,
                "service_filter": service
            }
            
            logger.info(
                f"Generated error statistics: {total_errors} total errors, "
                f"{unique_error_groups} unique groups, {affected_users} affected users"
            )
            
            return statistics
        
        except GoogleAPIError as e:
            logger.error(f"Error calculating error statistics: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calculating error statistics: {e}")
            raise
    
    def _format_error_event(self, event: Any) -> Dict[str, Any]:
        """
        Format error event data for API response.
        
        Args:
            event: Error event from Cloud Error Reporting
        
        Returns:
            Formatted error event dictionary
        """
        try:
            formatted = {
                "event_time": event.event_time.isoformat() if hasattr(event, 'event_time') and event.event_time else None,
                "message": event.message if hasattr(event, 'message') else None,
            }
            
            # Add service context
            if hasattr(event, 'service_context') and event.service_context:
                formatted["service_context"] = {
                    "service": event.service_context.service,
                    "version": event.service_context.version if hasattr(event.service_context, 'version') else None
                }
            
            # Add error context
            if hasattr(event, 'context') and event.context:
                context = {}
                
                if hasattr(event.context, 'http_request') and event.context.http_request:
                    context["http_request"] = {
                        "method": event.context.http_request.method,
                        "url": event.context.http_request.url,
                        "user_agent": event.context.http_request.user_agent,
                        "referrer": event.context.http_request.referrer,
                        "response_status_code": event.context.http_request.response_status_code
                    }
                
                if hasattr(event.context, 'user') and event.context.user:
                    context["user"] = event.context.user
                
                if hasattr(event.context, 'report_location') and event.context.report_location:
                    context["report_location"] = {
                        "file_path": event.context.report_location.file_path,
                        "line_number": event.context.report_location.line_number,
                        "function_name": event.context.report_location.function_name
                    }
                
                if hasattr(event.context, 'source_references') and event.context.source_references:
                    context["source_references"] = [
                        {
                            "repository": ref.repository,
                            "revision_id": ref.revision_id
                        }
                        for ref in event.context.source_references
                    ]
                
                formatted["context"] = context
            
            return formatted
        
        except Exception as e:
            logger.warning(f"Error formatting error event: {e}")
            return {
                "event_time": None,
                "message": str(event) if event else None
            }
    
    async def close(self):
        """Close client connections"""
        # Cloud clients don't need explicit closing in current SDK version
        pass
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
