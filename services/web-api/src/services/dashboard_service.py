"""Dashboard service for custom monitoring dashboards."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.monitoring import DashboardConfiguration
from src.models.monitoring_schemas import (
    DashboardCreate,
    DashboardUpdate,
    WidgetDataSource,
    WidgetDataPoint
)
from src.services.metrics_service import MetricsService
from src.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for managing custom monitoring dashboards."""
    
    def __init__(self, db_session: AsyncSession, project_id: str):
        """
        Initialize dashboard service.
        
        Args:
            db_session: Database session
            project_id: GCP project ID
        """
        self.db = db_session
        self.project_id = project_id
        self.metrics_service = MetricsService(project_id)
    
    async def create_dashboard(
        self,
        user_id: UUID,
        dashboard_data: DashboardCreate
    ) -> DashboardConfiguration:
        """
        Create a new dashboard.
        
        Args:
            user_id: User ID creating the dashboard
            dashboard_data: Dashboard creation data
        
        Returns:
            Created dashboard configuration
        """
        # Serialize widgets to JSON
        widgets_json = [widget.model_dump() for widget in dashboard_data.widgets]
        
        dashboard = DashboardConfiguration(
            user_id=user_id,
            name=dashboard_data.name,
            description=dashboard_data.description,
            layout=dashboard_data.layout,
            widgets=widgets_json,
            is_public=dashboard_data.is_public
        )
        
        # Generate share token if public
        if dashboard_data.is_public:
            dashboard.generate_share_token()
        
        self.db.add(dashboard)
        await self.db.commit()
        await self.db.refresh(dashboard)
        
        logger.info(f"Created dashboard {dashboard.id} for user {user_id}")
        return dashboard
    
    async def get_dashboard(
        self,
        dashboard_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[DashboardConfiguration]:
        """
        Get a dashboard by ID.
        
        Args:
            dashboard_id: Dashboard ID
            user_id: User ID (for ownership check, optional for public dashboards)
        
        Returns:
            Dashboard configuration or None if not found
        """
        query = select(DashboardConfiguration).where(
            DashboardConfiguration.id == dashboard_id
        )
        
        # If user_id provided, check ownership or public status
        if user_id is not None:
            query = query.where(
                or_(
                    DashboardConfiguration.user_id == user_id,
                    DashboardConfiguration.is_public == True
                )
            )
        else:
            # If no user_id, only return public dashboards
            query = query.where(DashboardConfiguration.is_public == True)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_dashboard_by_share_token(
        self,
        share_token: str
    ) -> Optional[DashboardConfiguration]:
        """
        Get a public dashboard by share token.
        
        Args:
            share_token: Share token
        
        Returns:
            Dashboard configuration or None if not found
        """
        query = select(DashboardConfiguration).where(
            and_(
                DashboardConfiguration.share_token == share_token,
                DashboardConfiguration.is_public == True
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_dashboards(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[DashboardConfiguration], int]:
        """
        List dashboards for a user.
        
        Args:
            user_id: User ID
            page: Page number
            page_size: Number of items per page
        
        Returns:
            Tuple of (dashboards, total_count)
        """
        # Build query
        query = select(DashboardConfiguration).where(
            DashboardConfiguration.user_id == user_id
        )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(
            DashboardConfiguration.updated_at.desc()
        ).offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        dashboards = result.scalars().all()
        
        return list(dashboards), total
    
    async def update_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        dashboard_data: DashboardUpdate
    ) -> Optional[DashboardConfiguration]:
        """
        Update a dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            user_id: User ID (for ownership check)
            dashboard_data: Dashboard update data
        
        Returns:
            Updated dashboard configuration or None if not found
        """
        # Get existing dashboard
        dashboard = await self.get_dashboard(dashboard_id, user_id)
        if not dashboard or dashboard.user_id != user_id:
            return None
        
        # Update fields
        update_data = dashboard_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == 'widgets' and value is not None:
                # Serialize widgets to JSON
                value = [widget.model_dump() for widget in value]
            setattr(dashboard, field, value)
        
        # Update share token if changing to public
        if dashboard_data.is_public is True and not dashboard.share_token:
            dashboard.generate_share_token()
        elif dashboard_data.is_public is False:
            dashboard.share_token = None
        
        dashboard.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(dashboard)
        
        logger.info(f"Updated dashboard {dashboard_id}")
        return dashboard
    
    async def delete_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            user_id: User ID (for ownership check)
        
        Returns:
            True if deleted, False if not found or not owned by user
        """
        # Get existing dashboard
        dashboard = await self.get_dashboard(dashboard_id, user_id)
        if not dashboard or dashboard.user_id != user_id:
            return False
        
        await self.db.delete(dashboard)
        await self.db.commit()
        
        logger.info(f"Deleted dashboard {dashboard_id}")
        return True
    
    async def generate_share_token(
        self,
        dashboard_id: UUID,
        user_id: UUID
    ) -> Optional[str]:
        """
        Generate or regenerate a share token for a dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            user_id: User ID (for ownership check)
        
        Returns:
            Share token or None if dashboard not found
        """
        # Get existing dashboard
        dashboard = await self.get_dashboard(dashboard_id, user_id)
        if not dashboard or dashboard.user_id != user_id:
            return None
        
        # Make dashboard public and generate token
        dashboard.is_public = True
        share_token = dashboard.generate_share_token()
        dashboard.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(f"Generated share token for dashboard {dashboard_id}")
        return share_token
    
    async def copy_dashboard(
        self,
        source_dashboard_id: UUID,
        user_id: UUID,
        new_name: str
    ) -> Optional[DashboardConfiguration]:
        """
        Copy a dashboard to the user's account.
        
        Args:
            source_dashboard_id: Source dashboard ID
            user_id: User ID creating the copy
            new_name: Name for the copied dashboard
        
        Returns:
            Copied dashboard configuration or None if source not found
        """
        # Get source dashboard (must be public or owned by user)
        source = await self.get_dashboard(source_dashboard_id, user_id)
        if not source:
            return None
        
        # Create copy
        copied_dashboard = DashboardConfiguration(
            user_id=user_id,
            name=new_name,
            description=source.description,
            layout=source.layout.copy() if source.layout else {},
            widgets=source.widgets.copy() if source.widgets else [],
            is_public=False  # Copies are private by default
        )
        
        self.db.add(copied_dashboard)
        await self.db.commit()
        await self.db.refresh(copied_dashboard)
        
        logger.info(
            f"Copied dashboard {source_dashboard_id} to {copied_dashboard.id} "
            f"for user {user_id}"
        )
        return copied_dashboard
    
    async def get_widget_data(
        self,
        data_source: WidgetDataSource
    ) -> List[WidgetDataPoint]:
        """
        Fetch data for a widget based on its data source configuration.
        
        Args:
            data_source: Widget data source configuration
        
        Returns:
            List of data points
        """
        # Check cache first
        cache_key = self._get_widget_cache_key(data_source)
        
        async with CacheService() as cache:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for widget data: {cache_key}")
                return [WidgetDataPoint(**point) for point in cached_data]
        
        # Parse time range
        end_time = datetime.utcnow()
        start_time = self._parse_time_range(data_source.time_range, end_time)
        
        # Fetch metrics from Cloud Monitoring
        time_series = await self.metrics_service.get_time_series(
            metric_type=data_source.metric_type,
            start_time=start_time,
            end_time=end_time,
            aggregation=data_source.aggregation,
            service_name=data_source.service_name
        )
        
        # Convert to data points
        data_points = [
            WidgetDataPoint(
                timestamp=point['timestamp'],
                value=point['value']
            )
            for point in time_series
        ]
        
        # Cache the result (TTL based on time range)
        cache_ttl = self._get_cache_ttl(data_source.time_range)
        async with CacheService() as cache:
            await cache.set(
                cache_key,
                [point.model_dump() for point in data_points],
                ttl=cache_ttl
            )
        
        logger.debug(
            f"Fetched {len(data_points)} data points for widget "
            f"(metric={data_source.metric_type}, range={data_source.time_range})"
        )
        
        return data_points
    
    def _get_widget_cache_key(self, data_source: WidgetDataSource) -> str:
        """Generate cache key for widget data."""
        parts = [
            "widget_data",
            data_source.metric_type,
            data_source.service_name or "all",
            data_source.aggregation,
            data_source.time_range
        ]
        return ":".join(parts)
    
    def _parse_time_range(self, time_range: str, end_time: datetime) -> datetime:
        """
        Parse time range string to start time.
        
        Args:
            time_range: Time range string (e.g., '1h', '24h', '7d', '30d')
            end_time: End time
        
        Returns:
            Start time
        """
        # Parse time range
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            return end_time - timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            return end_time - timedelta(days=days)
        else:
            # Default to 1 hour
            return end_time - timedelta(hours=1)
    
    def _get_cache_ttl(self, time_range: str) -> int:
        """
        Get cache TTL based on time range.
        
        Args:
            time_range: Time range string
        
        Returns:
            Cache TTL in seconds
        """
        # Shorter time ranges get shorter cache TTL
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            if hours <= 1:
                return 60  # 1 minute for 1 hour range
            elif hours <= 6:
                return 300  # 5 minutes for up to 6 hours
            else:
                return 600  # 10 minutes for longer hour ranges
        elif time_range.endswith('d'):
            return 1800  # 30 minutes for day ranges
        else:
            return 300  # Default 5 minutes
