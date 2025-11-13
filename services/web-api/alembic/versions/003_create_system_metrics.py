"""create system_metrics table

Revision ID: 003
Revises: 002
Create Date: 2024-01-08 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create system_metrics table with indexes and partitioning support."""
    op.create_table(
        'system_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_name', sa.String(length=100), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('metric_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient time-series queries
    op.create_index('idx_metrics_service_time', 'system_metrics', ['service_name', 'timestamp'])
    op.create_index('idx_metrics_type_time', 'system_metrics', ['metric_type', 'timestamp'])
    op.create_index('idx_metrics_timestamp', 'system_metrics', ['timestamp'])
    
    # Note: Time-series partitioning can be added later using pg_partman or manual partitioning
    # For now, we'll use indexes for performance. Partitioning should be implemented when
    # the table grows large (millions of rows).


def downgrade() -> None:
    """Drop system_metrics table."""
    op.drop_index('idx_metrics_timestamp', table_name='system_metrics')
    op.drop_index('idx_metrics_type_time', table_name='system_metrics')
    op.drop_index('idx_metrics_service_time', table_name='system_metrics')
    op.drop_table('system_metrics')
