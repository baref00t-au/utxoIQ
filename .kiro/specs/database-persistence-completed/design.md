# Design Document

## Overview

This design implements a persistent storage layer for the utxoIQ platform using Cloud SQL (PostgreSQL) for relational data and Redis (Memorystore) for caching. The system will store backfill job metadata, user feedback on insights, and system metrics while maintaining sub-100ms query performance through intelligent caching strategies.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   FastAPI App   │
│   (web-api)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ Redis │ │Cloud  │
│ Cache │ │SQL    │
│       │ │(PG)   │
└───────┘ └───┬───┘
              │
         ┌────▼────┐
         │ Cloud   │
         │ Storage │
         │(Backups)│
         └─────────┘
```

### Data Flow

1. **Write Path**: API → Database → Cache Invalidation
2. **Read Path**: API → Cache Check → Database (on miss) → Cache Update
3. **Backup Path**: Database → Cloud Storage (daily)
4. **Retention Path**: Database → Archive → Cold Storage

## Components and Interfaces

### 1. Database Models (SQLAlchemy)

#### BackfillJob Model
```python
class BackfillJob(Base):
    __tablename__ = "backfill_jobs"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    job_type = Column(String(50), nullable=False)  # 'blocks', 'transactions', etc.
    start_block = Column(Integer, nullable=False)
    end_block = Column(Integer, nullable=False)
    current_block = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)  # 'running', 'completed', 'failed', 'paused'
    progress_percentage = Column(Float, default=0.0)
    estimated_completion = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index('idx_backfill_status', 'status'),
        Index('idx_backfill_started', 'started_at'),
    )
```

#### InsightFeedback Model
```python
class InsightFeedback(Base):
    __tablename__ = "insight_feedback"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    insight_id = Column(String(100), nullable=False)
    user_id = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    comment = Column(Text, nullable=True)
    flag_type = Column(String(50), nullable=True)  # 'inaccurate', 'misleading', 'spam'
    flag_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_feedback_insight', 'insight_id'),
        Index('idx_feedback_user', 'user_id'),
        Index('idx_feedback_created', 'created_at'),
        UniqueConstraint('insight_id', 'user_id', name='uq_insight_user_feedback'),
    )
```

#### SystemMetric Model
```python
class SystemMetric(Base):
    __tablename__ = "system_metrics"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    service_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)  # 'cpu', 'memory', 'latency', etc.
    metric_value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # 'percent', 'ms', 'bytes'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    __table_args__ = (
        Index('idx_metrics_service_time', 'service_name', 'timestamp'),
        Index('idx_metrics_type_time', 'metric_type', 'timestamp'),
        # Partition by month for time-series data
    )
```

### 2. Database Service Layer

#### DatabaseService Interface
```python
class DatabaseService:
    def __init__(self, connection_string: str, pool_size: int = 10):
        """Initialize database connection pool"""
        
    async def create_backfill_job(self, job_data: BackfillJobCreate) -> BackfillJob:
        """Create new backfill job record"""
        
    async def update_backfill_progress(self, job_id: UUID, progress: float, current_block: int) -> BackfillJob:
        """Update backfill job progress"""
        
    async def get_backfill_job(self, job_id: UUID) -> Optional[BackfillJob]:
        """Retrieve backfill job by ID"""
        
    async def list_backfill_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[BackfillJob]:
        """List backfill jobs with optional status filter"""
        
    async def create_feedback(self, feedback_data: FeedbackCreate) -> InsightFeedback:
        """Create or update insight feedback"""
        
    async def get_feedback_stats(self, insight_id: str) -> FeedbackStats:
        """Get aggregated feedback statistics for an insight"""
        
    async def record_metric(self, metric_data: MetricCreate) -> SystemMetric:
        """Record system metric"""
        
    async def get_metrics(self, service: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[SystemMetric]:
        """Query metrics for time range"""
```

### 3. Cache Service Layer

#### CacheService Interface
```python
class CacheService:
    def __init__(self, redis_url: str):
        """Initialize Redis connection"""
        
    async def get(self, key: str) -> Optional[str]:
        """Get cached value"""
        
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set cached value with TTL"""
        
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        
    async def get_feedback_stats(self, insight_id: str) -> Optional[FeedbackStats]:
        """Get cached feedback stats"""
        
    async def cache_feedback_stats(self, insight_id: str, stats: FeedbackStats, ttl: int = 3600) -> bool:
        """Cache feedback statistics"""
        
    async def invalidate_feedback_cache(self, insight_id: str) -> bool:
        """Invalidate feedback cache on update"""
```

### 4. Migration System

#### Alembic Configuration
```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.models import Base

def run_migrations_online():
    """Run migrations in 'online' mode"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
```

#### Migration Scripts Structure
```
alembic/
├── versions/
│   ├── 001_create_backfill_jobs.py
│   ├── 002_create_insight_feedback.py
│   ├── 003_create_system_metrics.py
│   └── 004_add_indexes.py
├── env.py
└── script.py.mako
```

## Data Models

### Pydantic Schemas

#### Request/Response Models
```python
class BackfillJobCreate(BaseModel):
    job_type: str
    start_block: int
    end_block: int
    created_by: Optional[str] = None

class BackfillJobUpdate(BaseModel):
    current_block: int
    progress_percentage: float
    estimated_completion: Optional[datetime] = None
    status: Optional[str] = None
    error_message: Optional[str] = None

class BackfillJobResponse(BaseModel):
    id: UUID
    job_type: str
    start_block: int
    end_block: int
    current_block: int
    status: str
    progress_percentage: float
    estimated_completion: Optional[datetime]
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class FeedbackCreate(BaseModel):
    insight_id: str
    user_id: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    flag_type: Optional[str] = None
    flag_reason: Optional[str] = None

class FeedbackStats(BaseModel):
    insight_id: str
    total_ratings: int
    average_rating: float
    rating_distribution: Dict[int, int]
    total_comments: int
    total_flags: int
    flag_types: Dict[str, int]

class MetricCreate(BaseModel):
    service_name: str
    metric_type: str
    metric_value: float
    unit: str
    metadata: Optional[Dict[str, Any]] = None
```

### Cache Key Patterns

```python
CACHE_KEYS = {
    "feedback_stats": "feedback:stats:{insight_id}",
    "backfill_job": "backfill:job:{job_id}",
    "recent_metrics": "metrics:{service}:{metric_type}:recent",
}

CACHE_TTL = {
    "feedback_stats": 3600,  # 1 hour
    "backfill_job": 300,     # 5 minutes
    "recent_metrics": 300,   # 5 minutes
}
```

## Error Handling

### Database Error Handling
```python
class DatabaseError(Exception):
    """Base database error"""
    pass

class ConnectionError(DatabaseError):
    """Database connection failed"""
    pass

class QueryError(DatabaseError):
    """Query execution failed"""
    pass

class IntegrityError(DatabaseError):
    """Data integrity constraint violated"""
    pass

# Error handling pattern
async def safe_db_operation(operation: Callable) -> Tuple[Optional[Any], Optional[str]]:
    try:
        result = await operation()
        return result, None
    except IntegrityError as e:
        logger.error(f"Integrity error: {e}")
        return None, "Data constraint violation"
    except QueryError as e:
        logger.error(f"Query error: {e}")
        return None, "Database query failed"
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return None, "Database connection failed"
```

### Cache Fallback Strategy
```python
async def get_with_fallback(cache_key: str, db_query: Callable) -> Any:
    """Try cache first, fallback to database"""
    try:
        cached = await cache_service.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache error: {e}, falling back to database")
    
    # Fallback to database
    result = await db_query()
    
    # Try to cache result (best effort)
    try:
        await cache_service.set(cache_key, json.dumps(result), ttl=300)
    except Exception as e:
        logger.warning(f"Failed to cache result: {e}")
    
    return result
```

## Testing Strategy

### Unit Tests
- Database model validation
- Cache key generation
- TTL calculation logic
- Error handling paths

### Integration Tests
- Database CRUD operations
- Cache hit/miss scenarios
- Connection pool behavior
- Migration up/down operations

### Performance Tests
- Query latency under load
- Cache hit rate measurement
- Connection pool saturation
- Concurrent write operations

### Test Data Fixtures
```python
@pytest.fixture
async def db_session():
    """Provide test database session"""
    engine = create_async_engine("postgresql://test:test@localhost/test_db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession)
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def cache_service():
    """Provide test Redis cache"""
    cache = CacheService("redis://localhost:6379/1")
    yield cache
    await cache.flushdb()
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/utxoiq
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Backup
BACKUP_BUCKET=utxoiq-backups
BACKUP_SCHEDULE="0 1 * * *"  # Daily at 1 AM UTC
BACKUP_RETENTION_DAYS=7

# Retention
METRICS_RETENTION_DAYS=90
FEEDBACK_RETENTION_DAYS=730
BACKFILL_RETENTION_DAYS=180
```

### Connection Pool Configuration
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,           # Minimum connections
    max_overflow=20,        # Additional connections under load
    pool_timeout=30,        # Wait time for connection
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True,     # Verify connections before use
    echo=False,             # Disable SQL logging in production
)
```

## Deployment Considerations

### Cloud SQL Setup
- Instance type: db-custom-2-7680 (2 vCPU, 7.5 GB RAM)
- Storage: 100 GB SSD with automatic increase
- High availability: Regional instance with failover replica
- Backup: Automated daily backups with 7-day retention
- Maintenance window: Sunday 02:00-03:00 UTC

### Redis (Memorystore) Setup
- Tier: Standard (high availability)
- Memory: 5 GB
- Version: Redis 7.0
- Eviction policy: allkeys-lru
- Persistence: RDB snapshots every 6 hours

### Monitoring
- Cloud SQL metrics: CPU, memory, connections, query latency
- Redis metrics: Hit rate, memory usage, evicted keys
- Custom metrics: Cache hit rate, query performance, pool utilization
- Alerts: Connection pool exhaustion, high query latency, backup failures
