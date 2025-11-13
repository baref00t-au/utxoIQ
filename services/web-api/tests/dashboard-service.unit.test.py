"""Tests for dashboard service."""
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.dashboard_service import DashboardService
from src.models.monitoring import DashboardConfiguration
from src.models.monitoring_schemas import (
    DashboardCreate,
    DashboardUpdate,
    WidgetConfig,
    WidgetDataSource,
    WidgetDisplayOptions,
    WidgetDataPoint
)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def dashboard_service(mock_db_session):
    """Create a dashboard service instance."""
    return DashboardService(
        db_session=mock_db_session,
        project_id="test-project"
    )


@pytest.fixture
def sample_widget_config():
    """Create a sample widget configuration."""
    return WidgetConfig(
        id="widget-1",
        type="line_chart",
        title="API Response Time",
        data_source=WidgetDataSource(
            metric_type="custom.googleapis.com/api/response_time",
            aggregation="ALIGN_MEAN",
            time_range="1h"
        ),
        display_options=WidgetDisplayOptions(
            show_legend=True,
            y_axis_label="Milliseconds",
            color="#FF5A21"
        ),
        position={"x": 0, "y": 0, "w": 6, "h": 4}
    )


@pytest.fixture
def sample_dashboard_create(sample_widget_config):
    """Create a sample dashboard creation request."""
    return DashboardCreate(
        name="Test Dashboard",
        description="Test dashboard description",
        layout={"cols": 12, "rowHeight": 100},
        widgets=[sample_widget_config],
        is_public=False
    )


class TestDashboardCreation:
    """Tests for dashboard creation."""
    
    @pytest.mark.asyncio
    async def test_create_dashboard_success(
        self,
        dashboard_service,
        mock_db_session,
        sample_dashboard_create
    ):
        """Test successful dashboard creation."""
        user_id = uuid4()
        
        # Mock database operations
        mock_db_session.refresh.side_effect = lambda obj: setattr(obj, 'id', uuid4())
        
        # Create dashboard
        dashboard = await dashboard_service.create_dashboard(
            user_id=user_id,
            dashboard_data=sample_dashboard_create
        )
        
        # Verify dashboard was created
        assert dashboard.name == "Test Dashboard"
        assert dashboard.description == "Test dashboard description"
        assert dashboard.user_id == user_id
        assert dashboard.is_public is False
        assert len(dashboard.widgets) == 1
        
        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_public_dashboard_generates_token(
        self,
        dashboard_service,
        mock_db_session,
        sample_dashboard_create
    ):
        """Test that creating a public dashboard generates a share token."""
        user_id = uuid4()
        sample_dashboard_create.is_public = True
        
        # Mock database operations
        mock_db_session.refresh.side_effect = lambda obj: setattr(obj, 'id', uuid4())
        
        # Create dashboard
        dashboard = await dashboard_service.create_dashboard(
            user_id=user_id,
            dashboard_data=sample_dashboard_create
        )
        
        # Verify share token was generated
        assert dashboard.is_public is True
        assert dashboard.share_token is not None
        assert len(dashboard.share_token) > 0


class TestDashboardRetrieval:
    """Tests for dashboard retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_dashboard_by_owner(
        self,
        dashboard_service,
        mock_db_session
    ):
        """Test retrieving a dashboard by owner."""
        dashboard_id = uuid4()
        user_id = uuid4()
        
        # Mock dashboard
        mock_dashboard = DashboardConfiguration(
            id=dashboard_id,
            user_id=user_id,
            name="Test Dashboard",
            layout={},
            widgets=[],
            is_public=False
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db_session.execute.return_value = mock_result
        
        # Get dashboard
        dashboard = await dashboard_service.get_dashboard(
            dashboard_id=dashboard_id,
            user_id=user_id
        )
        
        # Verify dashboard was retrieved
        assert dashboard is not None
        assert dashboard.id == dashboard_id
        assert dashboard.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_get_public_dashboard_without_user(
        self,
        dashboard_service,
        mock_db_session
    ):
        """Test retrieving a public dashboard without user ID."""
        dashboard_id = uuid4()
        
        # Mock public dashboard
        mock_dashboard = DashboardConfiguration(
            id=dashboard_id,
            user_id=uuid4(),
            name="Public Dashboard",
            layout={},
            widgets=[],
            is_public=True,
            share_token="test-token"
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db_session.execute.return_value = mock_result
        
        # Get dashboard without user ID
        dashboard = await dashboard_service.get_dashboard(
            dashboard_id=dashboard_id,
            user_id=None
        )
        
        # Verify dashboard was retrieved
        assert dashboard is not None
        assert dashboard.is_public is True
    
    @pytest.mark.asyncio
    async def test_get_dashboard_by_share_token(
        self,
        dashboard_service,
        mock_db_session
    ):
        """Test retrieving a dashboard by share token."""
        share_token = "test-share-token"
        
        # Mock public dashboard
        mock_dashboard = DashboardConfiguration(
            id=uuid4(),
            user_id=uuid4(),
            name="Shared Dashboard",
            layout={},
            widgets=[],
            is_public=True,
            share_token=share_token
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db_session.execute.return_value = mock_result
        
        # Get dashboard by share token
        dashboard = await dashboard_service.get_dashboard_by_share_token(
            share_token=share_token
        )
        
        # Verify dashboard was retrieved
        assert dashboard is not None
        assert dashboard.share_token == share_token
        assert dashboard.is_public is True


class TestDashboardUpdate:
    """Tests for dashboard updates."""
    
    @pytest.mark.asyncio
    async def test_update_dashboard_name(
        self,
        dashboard_service,
        mock_db_session
    ):
        """Test updating dashboard name."""
        dashboard_id = uuid4()
        user_id = uuid4()
        
        # Mock existing dashboard
        mock_dashboard = DashboardConfiguration(
            id=dashboard_id,
            user_id=user_id,
            name="Old Name",
            layout={},
            widgets=[],
            is_public=False
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db_session.execute.return_value = mock_result
        
        # Update dashboard
        update_data = DashboardUpdate(name="New Name")
        dashboard = await dashboard_service.update_dashboard(
            dashboard_id=dashboard_id,
            user_id=user_id,
            dashboard_data=update_data
        )
        
        # Verify dashboard was updated
        assert dashboard is not None
        assert dashboard.name == "New Name"
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_dashboard_to_public_generates_token(
        self,
        dashboard_service,
        mock_db_session
    ):
        """Test that updating a dashboard to public generates a share token."""
        dashboard_id = uuid4()
        user_id = uuid4()
        
        # Mock existing private dashboard
        mock_dashboard = DashboardConfiguration(
            id=dashboard_id,
            user_id=user_id,
            name="Test Dashboard",
            layout={},
            widgets=[],
            is_public=False,
            share_token=None
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db_session.execute.return_value = mock_result
        
        # Update dashboard to public
        update_data = DashboardUpdate(is_public=True)
        dashboard = await dashboard_service.update_dashboard(
            dashboard_id=dashboard_id,
            user_id=user_id,
            dashboard_data=update_data
        )
        
        # Verify share token was generated
        assert dashboard is not None
        assert dashboard.is_public is True
        assert dashboard.share_token is not None


class TestDashboardDeletion:
    """Tests for dashboard deletion."""
    
    @pytest.mark.asyncio
    async def test_delete_dashboard_success(
        self,
        dashboard_service,
        mock_db_session
    ):
        """Test successful dashboard deletion."""
        dashboard_id = uuid4()
        user_id = uuid4()
        
        # Mock existing dashboard
        mock_dashboard = DashboardConfiguration(
            id=dashboard_id,
            user_id=user_id,
            name="Test Dashboard",
            layout={},
            widgets=[],
            is_public=False
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db_session.execute.return_value = mock_result
        
        # Delete dashboard
        deleted = await dashboard_service.delete_dashboard(
            dashboard_id=dashboard_id,
            user_id=user_id
        )
        
        # Verify dashboard was deleted
        assert deleted is True
        mock_db_session.delete.assert_called_once_with(mock_dashboard)
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_dashboard_not_owned(
        self,
        dashboard_service,
        mock_db_session
    ):
        """Test deleting a dashboard not owned by user."""
        dashboard_id = uuid4()
        user_id = uuid4()
        other_user_id = uuid4()
        
        # Mock dashboard owned by different user
        mock_dashboard = DashboardConfiguration(
            id=dashboard_id,
            user_id=other_user_id,
            name="Test Dashboard",
            layout={},
            widgets=[],
            is_public=False
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db_session.execute.return_value = mock_result
        
        # Attempt to delete dashboard
        deleted = await dashboard_service.delete_dashboard(
            dashboard_id=dashboard_id,
            user_id=user_id
        )
        
        # Verify dashboard was not deleted
        assert deleted is False
        mock_db_session.delete.assert_not_called()


class TestDashboardSharing:
    """Tests for dashboard sharing."""
    
    @pytest.mark.asyncio
    async def test_generate_share_token(
        self,
        dashboard_service,
        mock_db_session
    ):
        """Test generating a share token."""
        dashboard_id = uuid4()
        user_id = uuid4()
        
        # Mock existing dashboard
        mock_dashboard = DashboardConfiguration(
            id=dashboard_id,
            user_id=user_id,
            name="Test Dashboard",
            layout={},
            widgets=[],
            is_public=False,
            share_token=None
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db_session.execute.return_value = mock_result
        
        # Generate share token
        share_token = await dashboard_service.generate_share_token(
            dashboard_id=dashboard_id,
            user_id=user_id
        )
        
        # Verify share token was generated
        assert share_token is not None
        assert len(share_token) > 0
        assert mock_dashboard.is_public is True
        assert mock_dashboard.share_token == share_token
        mock_db_session.commit.assert_called_once()


class TestDashboardCopy:
    """Tests for dashboard copying."""
    
    @pytest.mark.asyncio
    async def test_copy_dashboard_success(
        self,
        dashboard_service,
        mock_db_session
    ):
        """Test successful dashboard copying."""
        source_id = uuid4()
        user_id = uuid4()
        
        # Mock source dashboard
        mock_source = DashboardConfiguration(
            id=source_id,
            user_id=user_id,
            name="Source Dashboard",
            description="Source description",
            layout={"cols": 12},
            widgets=[{"id": "widget-1", "type": "line_chart"}],
            is_public=True
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_source
        mock_db_session.execute.return_value = mock_result
        mock_db_session.refresh.side_effect = lambda obj: setattr(obj, 'id', uuid4())
        
        # Copy dashboard
        copied = await dashboard_service.copy_dashboard(
            source_dashboard_id=source_id,
            user_id=user_id,
            new_name="Copied Dashboard"
        )
        
        # Verify dashboard was copied
        assert copied is not None
        assert copied.name == "Copied Dashboard"
        assert copied.description == "Source description"
        assert copied.user_id == user_id
        assert copied.is_public is False  # Copies are private by default
        assert len(copied.widgets) == 1
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()


class TestWidgetData:
    """Tests for widget data fetching."""
    
    @pytest.mark.asyncio
    async def test_get_widget_data_with_cache_hit(
        self,
        dashboard_service
    ):
        """Test getting widget data with cache hit."""
        data_source = WidgetDataSource(
            metric_type="custom.googleapis.com/api/response_time",
            aggregation="ALIGN_MEAN",
            time_range="1h"
        )
        
        # Mock cached data
        cached_data = [
            {"timestamp": "2024-01-15T10:00:00Z", "value": 125.5},
            {"timestamp": "2024-01-15T10:05:00Z", "value": 130.2}
        ]
        
        with patch('src.services.dashboard_service.CacheService') as mock_cache_class:
            mock_cache = AsyncMock()
            mock_cache.__aenter__.return_value = mock_cache
            mock_cache.__aexit__.return_value = None
            mock_cache.get.return_value = cached_data
            mock_cache_class.return_value = mock_cache
            
            # Get widget data
            data_points = await dashboard_service.get_widget_data(data_source)
            
            # Verify data was returned from cache
            assert len(data_points) == 2
            assert data_points[0].timestamp == "2024-01-15T10:00:00Z"
            assert data_points[0].value == 125.5
            mock_cache.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_time_range_hours(self, dashboard_service):
        """Test parsing time range in hours."""
        end_time = datetime(2024, 1, 15, 12, 0, 0)
        
        # Test 1 hour
        start_time = dashboard_service._parse_time_range("1h", end_time)
        assert (end_time - start_time).total_seconds() == 3600
        
        # Test 6 hours
        start_time = dashboard_service._parse_time_range("6h", end_time)
        assert (end_time - start_time).total_seconds() == 6 * 3600
    
    @pytest.mark.asyncio
    async def test_parse_time_range_days(self, dashboard_service):
        """Test parsing time range in days."""
        end_time = datetime(2024, 1, 15, 12, 0, 0)
        
        # Test 1 day
        start_time = dashboard_service._parse_time_range("1d", end_time)
        assert (end_time - start_time).days == 1
        
        # Test 7 days
        start_time = dashboard_service._parse_time_range("7d", end_time)
        assert (end_time - start_time).days == 7
    
    @pytest.mark.asyncio
    async def test_get_cache_ttl(self, dashboard_service):
        """Test getting cache TTL based on time range."""
        # Short ranges get short TTL
        assert dashboard_service._get_cache_ttl("1h") == 60
        assert dashboard_service._get_cache_ttl("6h") == 300
        
        # Longer ranges get longer TTL
        assert dashboard_service._get_cache_ttl("24h") == 600
        assert dashboard_service._get_cache_ttl("7d") == 1800


class TestWidgetConfigValidation:
    """Tests for widget configuration validation."""
    
    def test_widget_config_valid(self, sample_widget_config):
        """Test valid widget configuration."""
        assert sample_widget_config.id == "widget-1"
        assert sample_widget_config.type == "line_chart"
        assert sample_widget_config.title == "API Response Time"
    
    def test_dashboard_create_validates_unique_widget_ids(self):
        """Test that dashboard creation validates unique widget IDs."""
        widget1 = WidgetConfig(
            id="widget-1",
            type="line_chart",
            title="Widget 1",
            data_source=WidgetDataSource(
                metric_type="metric1",
                aggregation="ALIGN_MEAN",
                time_range="1h"
            )
        )
        
        widget2 = WidgetConfig(
            id="widget-1",  # Duplicate ID
            type="bar_chart",
            title="Widget 2",
            data_source=WidgetDataSource(
                metric_type="metric2",
                aggregation="ALIGN_MEAN",
                time_range="1h"
            )
        )
        
        # Should raise validation error for duplicate IDs
        with pytest.raises(ValueError, match="Widget IDs must be unique"):
            DashboardCreate(
                name="Test Dashboard",
                widgets=[widget1, widget2]
            )
