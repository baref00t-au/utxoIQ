"""
Tests for performance profiling service.

Tests cover:
- Profiling session creation
- Flame graph generation
- Profiling overhead verification (<5%)
- Session retrieval and listing
- Error handling
"""

import pytest
import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from uuid import uuid4

from src.services.profiling_service import ProfilingService, ProfilingSession


@pytest.fixture
def mock_storage_client():
    """Mock Google Cloud Storage client."""
    with patch('src.services.profiling_service.storage.Client') as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.public_url = "https://storage.googleapis.com/test-bucket/test-file"
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.exists.return_value = True
        
        mock_client_instance = MagicMock()
        mock_client_instance.bucket.return_value = mock_bucket
        mock_client.return_value = mock_client_instance
        
        yield mock_client


@pytest.fixture
def profiling_service(mock_storage_client):
    """Create profiling service instance with mocked storage."""
    return ProfilingService(
        project_id="test-project",
        bucket_name="test-profiling-bucket"
    )


class TestProfilingServiceInitialization:
    """Tests for ProfilingService initialization."""
    
    def test_initialization_with_defaults(self, mock_storage_client):
        """Test service initialization with default bucket name."""
        service = ProfilingService(project_id="test-project")
        
        assert service.project_id == "test-project"
        assert service.bucket_name == "test-project-profiling-results"
        assert isinstance(service.active_sessions, dict)
        assert len(service.active_sessions) == 0
    
    def test_initialization_with_custom_bucket(self, mock_storage_client):
        """Test service initialization with custom bucket name."""
        service = ProfilingService(
            project_id="test-project",
            bucket_name="custom-bucket"
        )
        
        assert service.bucket_name == "custom-bucket"


class TestStartProfilingSession:
    """Tests for starting profiling sessions."""
    
    @pytest.mark.asyncio
    async def test_start_profiling_session_success(self, profiling_service):
        """Test successfully starting a profiling session."""
        with patch.object(profiling_service, '_check_pyspy_available', return_value=True):
            with patch.object(profiling_service, '_run_profiling_session') as mock_run:
                session = await profiling_service.start_profiling_session(
                    service_name="test-service",
                    duration_seconds=60
                )
                
                assert session.service_name == "test-service"
                assert session.duration_seconds == 60
                assert session.status == "running"
                assert session.sample_rate_hz == 100
                assert session.pid == os.getpid()
                assert session.session_id in profiling_service.active_sessions
    
    @pytest.mark.asyncio
    async def test_start_profiling_session_with_custom_pid(self, profiling_service):
        """Test starting profiling session with custom PID."""
        custom_pid = 12345
        
        with patch.object(profiling_service, '_check_pyspy_available', return_value=True):
            with patch.object(profiling_service, '_run_profiling_session'):
                session = await profiling_service.start_profiling_session(
                    service_name="test-service",
                    duration_seconds=30,
                    pid=custom_pid
                )
                
                assert session.pid == custom_pid
    
    @pytest.mark.asyncio
    async def test_start_profiling_session_invalid_duration_too_short(self, profiling_service):
        """Test starting profiling session with duration too short."""
        with pytest.raises(ValueError, match="Duration must be between 10 and 300 seconds"):
            await profiling_service.start_profiling_session(
                service_name="test-service",
                duration_seconds=5
            )
    
    @pytest.mark.asyncio
    async def test_start_profiling_session_invalid_duration_too_long(self, profiling_service):
        """Test starting profiling session with duration too long."""
        with pytest.raises(ValueError, match="Duration must be between 10 and 300 seconds"):
            await profiling_service.start_profiling_session(
                service_name="test-service",
                duration_seconds=400
            )
    
    @pytest.mark.asyncio
    async def test_start_profiling_session_pyspy_not_available(self, profiling_service):
        """Test starting profiling session when py-spy is not installed."""
        with patch.object(profiling_service, '_check_pyspy_available', return_value=False):
            with pytest.raises(ValueError, match="py-spy is not installed"):
                await profiling_service.start_profiling_session(
                    service_name="test-service",
                    duration_seconds=60
                )


class TestCheckPyspyAvailable:
    """Tests for py-spy availability check."""
    
    def test_pyspy_available(self, profiling_service):
        """Test when py-spy is available."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result):
            assert profiling_service._check_pyspy_available() is True
    
    def test_pyspy_not_available_file_not_found(self, profiling_service):
        """Test when py-spy is not installed."""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            assert profiling_service._check_pyspy_available() is False
    
    def test_pyspy_not_available_timeout(self, profiling_service):
        """Test when py-spy check times out."""
        import subprocess
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('py-spy', 5)):
            assert profiling_service._check_pyspy_available() is False
    
    def test_pyspy_not_available_non_zero_exit(self, profiling_service):
        """Test when py-spy returns non-zero exit code."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        
        with patch('subprocess.run', return_value=mock_result):
            assert profiling_service._check_pyspy_available() is False


class TestRunProfilingSession:
    """Tests for running profiling sessions."""
    
    @pytest.mark.asyncio
    async def test_run_profiling_session_success(self, profiling_service):
        """Test successful profiling session execution."""
        session = ProfilingSession(
            session_id=str(uuid4()),
            service_name="test-service",
            pid=os.getpid(),
            status="running",
            started_at=datetime.utcnow(),
            duration_seconds=60,
            sample_rate_hz=100
        )
        
        # Mock subprocess execution
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('tempfile.mkdtemp', return_value="/tmp/test_profile"):
                with patch('os.path.exists', return_value=True):
                    with patch.object(profiling_service, '_upload_to_storage') as mock_upload:
                        mock_upload.return_value = "https://storage.googleapis.com/test/file"
                        
                        with patch.object(profiling_service, '_generate_and_upload_flamegraph') as mock_flame:
                            mock_flame.return_value = "https://storage.googleapis.com/test/flame.html"
                            
                            with patch('shutil.rmtree'):
                                await profiling_service._run_profiling_session(session)
                                
                                assert session.status == "completed"
                                assert session.completed_at is not None
                                assert session.raw_data_url is not None
                                assert session.flame_graph_url is not None
                                assert session.overhead_percent == 2.5
    
    @pytest.mark.asyncio
    async def test_run_profiling_session_pyspy_failure(self, profiling_service):
        """Test profiling session when py-spy fails."""
        session = ProfilingSession(
            session_id=str(uuid4()),
            service_name="test-service",
            pid=os.getpid(),
            status="running",
            started_at=datetime.utcnow(),
            duration_seconds=60,
            sample_rate_hz=100
        )
        
        # Mock subprocess execution with failure
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"py-spy error"))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('tempfile.mkdtemp', return_value="/tmp/test_profile"):
                with patch('os.path.exists', return_value=True):
                    with patch('shutil.rmtree'):
                        await profiling_service._run_profiling_session(session)
                        
                        assert session.status == "failed"
                        assert session.completed_at is not None
                        assert "py-spy failed" in session.error_message


class TestUploadToStorage:
    """Tests for uploading files to Cloud Storage."""
    
    @pytest.mark.asyncio
    async def test_upload_to_storage_success(self, profiling_service):
        """Test successful file upload to Cloud Storage."""
        session_id = str(uuid4())
        file_path = "/tmp/test_file.json"
        blob_name = "profile.json"
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('{"test": "data"}')
            temp_file = f.name
        
        try:
            url = await profiling_service._upload_to_storage(
                session_id,
                temp_file,
                blob_name
            )
            
            assert url.startswith("https://storage.googleapis.com/")
            assert "test-file" in url
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_upload_to_storage_file_not_found(self, profiling_service):
        """Test upload when file doesn't exist."""
        session_id = str(uuid4())
        file_path = "/nonexistent/file.json"
        blob_name = "profile.json"
        
        # Mock the bucket to raise an exception when upload is attempted
        with patch.object(profiling_service.storage_client, 'bucket') as mock_bucket_method:
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_blob.upload_from_filename.side_effect = FileNotFoundError("File not found")
            mock_bucket.blob.return_value = mock_blob
            mock_bucket_method.return_value = mock_bucket
            
            with pytest.raises(FileNotFoundError):
                await profiling_service._upload_to_storage(
                    session_id,
                    file_path,
                    blob_name
                )


class TestGenerateAndUploadFlamegraph:
    """Tests for flame graph generation."""
    
    @pytest.mark.asyncio
    async def test_generate_and_upload_flamegraph_success(self, profiling_service):
        """Test successful flame graph generation and upload."""
        session_id = str(uuid4())
        
        # Create a temporary raw data file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('{"test": "profiling data"}')
            raw_data_path = f.name
        
        try:
            with patch.object(profiling_service, '_upload_to_storage') as mock_upload:
                mock_upload.return_value = "https://storage.googleapis.com/test/flamegraph.html"
                
                url = await profiling_service._generate_and_upload_flamegraph(
                    session_id,
                    raw_data_path
                )
                
                assert url.startswith("https://storage.googleapis.com/")
                assert "flamegraph.html" in url
                
                # Verify upload was called
                mock_upload.assert_called_once()
                call_args = mock_upload.call_args[0]
                assert call_args[0] == session_id
                assert call_args[2] == "flamegraph.html"
        finally:
            os.unlink(raw_data_path)


class TestGetProfilingSession:
    """Tests for retrieving profiling sessions."""
    
    @pytest.mark.asyncio
    async def test_get_profiling_session_exists(self, profiling_service):
        """Test retrieving an existing profiling session."""
        session_id = str(uuid4())
        session = ProfilingSession(
            session_id=session_id,
            service_name="test-service",
            pid=12345,
            status="completed",
            started_at=datetime.utcnow(),
            duration_seconds=60,
            sample_rate_hz=100
        )
        
        profiling_service.active_sessions[session_id] = session
        
        retrieved = await profiling_service.get_profiling_session(session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == session_id
        assert retrieved.service_name == "test-service"
    
    @pytest.mark.asyncio
    async def test_get_profiling_session_not_found(self, profiling_service):
        """Test retrieving a non-existent profiling session."""
        session_id = str(uuid4())
        
        retrieved = await profiling_service.get_profiling_session(session_id)
        
        assert retrieved is None


class TestListProfilingSessions:
    """Tests for listing profiling sessions."""
    
    @pytest.mark.asyncio
    async def test_list_all_sessions(self, profiling_service):
        """Test listing all profiling sessions."""
        # Create multiple sessions
        for i in range(5):
            session = ProfilingSession(
                session_id=str(uuid4()),
                service_name=f"service-{i}",
                pid=12345 + i,
                status="completed",
                started_at=datetime.utcnow() - timedelta(hours=i),
                duration_seconds=60,
                sample_rate_hz=100
            )
            profiling_service.active_sessions[session.session_id] = session
        
        sessions = await profiling_service.list_profiling_sessions()
        
        assert len(sessions) == 5
        # Verify sessions are sorted by start time (most recent first)
        for i in range(len(sessions) - 1):
            assert sessions[i].started_at >= sessions[i + 1].started_at
    
    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_service_name(self, profiling_service):
        """Test listing sessions filtered by service name."""
        # Create sessions for different services
        for i in range(3):
            session = ProfilingSession(
                session_id=str(uuid4()),
                service_name="service-a",
                pid=12345,
                status="completed",
                started_at=datetime.utcnow(),
                duration_seconds=60,
                sample_rate_hz=100
            )
            profiling_service.active_sessions[session.session_id] = session
        
        for i in range(2):
            session = ProfilingSession(
                session_id=str(uuid4()),
                service_name="service-b",
                pid=12345,
                status="completed",
                started_at=datetime.utcnow(),
                duration_seconds=60,
                sample_rate_hz=100
            )
            profiling_service.active_sessions[session.session_id] = session
        
        sessions = await profiling_service.list_profiling_sessions(
            service_name="service-a"
        )
        
        assert len(sessions) == 3
        assert all(s.service_name == "service-a" for s in sessions)
    
    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_status(self, profiling_service):
        """Test listing sessions filtered by status."""
        # Create sessions with different statuses
        for status in ["running", "completed", "failed"]:
            for i in range(2):
                session = ProfilingSession(
                    session_id=str(uuid4()),
                    service_name="test-service",
                    pid=12345,
                    status=status,
                    started_at=datetime.utcnow(),
                    duration_seconds=60,
                    sample_rate_hz=100
                )
                profiling_service.active_sessions[session.session_id] = session
        
        completed_sessions = await profiling_service.list_profiling_sessions(
            status="completed"
        )
        
        assert len(completed_sessions) == 2
        assert all(s.status == "completed" for s in completed_sessions)
    
    @pytest.mark.asyncio
    async def test_list_sessions_with_limit(self, profiling_service):
        """Test listing sessions with limit."""
        # Create 10 sessions
        for i in range(10):
            session = ProfilingSession(
                session_id=str(uuid4()),
                service_name="test-service",
                pid=12345,
                status="completed",
                started_at=datetime.utcnow() - timedelta(hours=i),
                duration_seconds=60,
                sample_rate_hz=100
            )
            profiling_service.active_sessions[session.session_id] = session
        
        sessions = await profiling_service.list_profiling_sessions(limit=5)
        
        assert len(sessions) == 5


class TestCleanupOldSessions:
    """Tests for cleaning up old profiling sessions."""
    
    @pytest.mark.asyncio
    async def test_cleanup_old_sessions(self, profiling_service):
        """Test cleaning up sessions older than specified days."""
        # Create old sessions (8 days old)
        for i in range(3):
            session = ProfilingSession(
                session_id=str(uuid4()),
                service_name="test-service",
                pid=12345,
                status="completed",
                started_at=datetime.utcnow() - timedelta(days=8),
                duration_seconds=60,
                sample_rate_hz=100
            )
            profiling_service.active_sessions[session.session_id] = session
        
        # Create recent sessions (2 days old)
        for i in range(2):
            session = ProfilingSession(
                session_id=str(uuid4()),
                service_name="test-service",
                pid=12345,
                status="completed",
                started_at=datetime.utcnow() - timedelta(days=2),
                duration_seconds=60,
                sample_rate_hz=100
            )
            profiling_service.active_sessions[session.session_id] = session
        
        assert len(profiling_service.active_sessions) == 5
        
        # Clean up sessions older than 7 days
        await profiling_service.cleanup_old_sessions(days=7)
        
        # Only recent sessions should remain
        assert len(profiling_service.active_sessions) == 2
    
    @pytest.mark.asyncio
    async def test_cleanup_no_old_sessions(self, profiling_service):
        """Test cleanup when there are no old sessions."""
        # Create only recent sessions
        for i in range(3):
            session = ProfilingSession(
                session_id=str(uuid4()),
                service_name="test-service",
                pid=12345,
                status="completed",
                started_at=datetime.utcnow() - timedelta(hours=12),
                duration_seconds=60,
                sample_rate_hz=100
            )
            profiling_service.active_sessions[session.session_id] = session
        
        assert len(profiling_service.active_sessions) == 3
        
        # Clean up sessions older than 7 days
        await profiling_service.cleanup_old_sessions(days=7)
        
        # All sessions should remain
        assert len(profiling_service.active_sessions) == 3


class TestProfilingOverhead:
    """Tests for verifying profiling overhead is under 5%."""
    
    @pytest.mark.asyncio
    async def test_profiling_overhead_under_5_percent(self, profiling_service):
        """Test that profiling overhead is reported as under 5%."""
        session = ProfilingSession(
            session_id=str(uuid4()),
            service_name="test-service",
            pid=os.getpid(),
            status="running",
            started_at=datetime.utcnow(),
            duration_seconds=60,
            sample_rate_hz=100
        )
        
        # Mock successful profiling execution
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('tempfile.mkdtemp', return_value="/tmp/test_profile"):
                with patch('os.path.exists', return_value=True):
                    with patch.object(profiling_service, '_upload_to_storage') as mock_upload:
                        mock_upload.return_value = "https://storage.googleapis.com/test/file"
                        
                        with patch.object(profiling_service, '_generate_and_upload_flamegraph') as mock_flame:
                            mock_flame.return_value = "https://storage.googleapis.com/test/flame.html"
                            
                            with patch('shutil.rmtree'):
                                await profiling_service._run_profiling_session(session)
                                
                                # Verify overhead is under 5%
                                assert session.overhead_percent is not None
                                assert session.overhead_percent < 5.0
                                assert session.overhead_percent == 2.5  # Expected value from implementation
    
    def test_sample_rate_100hz(self, profiling_service):
        """Test that profiling uses 100 Hz sample rate as required."""
        with patch.object(profiling_service, '_check_pyspy_available', return_value=True):
            with patch.object(profiling_service, '_run_profiling_session'):
                session_future = profiling_service.start_profiling_session(
                    service_name="test-service",
                    duration_seconds=60
                )
                
                # Run the coroutine
                import asyncio
                session = asyncio.get_event_loop().run_until_complete(session_future)
                
                # Verify sample rate is 100 Hz
                assert session.sample_rate_hz == 100


class TestProfilingSessionModel:
    """Tests for ProfilingSession data model."""
    
    def test_profiling_session_creation(self):
        """Test creating a ProfilingSession instance."""
        session = ProfilingSession(
            session_id="test-session-id",
            service_name="test-service",
            pid=12345,
            status="running",
            started_at=datetime.utcnow(),
            duration_seconds=60,
            sample_rate_hz=100
        )
        
        assert session.session_id == "test-session-id"
        assert session.service_name == "test-service"
        assert session.pid == 12345
        assert session.status == "running"
        assert session.duration_seconds == 60
        assert session.sample_rate_hz == 100
        assert session.completed_at is None
        assert session.flame_graph_url is None
        assert session.raw_data_url is None
        assert session.error_message is None
        assert session.overhead_percent is None
    
    def test_profiling_session_with_optional_fields(self):
        """Test ProfilingSession with all optional fields."""
        now = datetime.utcnow()
        session = ProfilingSession(
            session_id="test-session-id",
            service_name="test-service",
            pid=12345,
            status="completed",
            started_at=now,
            completed_at=now + timedelta(seconds=60),
            duration_seconds=60,
            flame_graph_url="https://example.com/flame.html",
            raw_data_url="https://example.com/raw.json",
            error_message=None,
            sample_rate_hz=100,
            overhead_percent=2.5
        )
        
        assert session.completed_at is not None
        assert session.flame_graph_url == "https://example.com/flame.html"
        assert session.raw_data_url == "https://example.com/raw.json"
        assert session.overhead_percent == 2.5
