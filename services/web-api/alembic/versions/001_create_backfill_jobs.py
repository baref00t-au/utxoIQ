"""create backfill_jobs table

Revision ID: 001
Revises: 
Create Date: 2024-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create backfill_jobs table with indexes."""
    op.create_table(
        'backfill_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('start_block', sa.Integer(), nullable=False),
        sa.Column('end_block', sa.Integer(), nullable=False),
        sa.Column('current_block', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('estimated_completion', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_backfill_status', 'backfill_jobs', ['status'])
    op.create_index('idx_backfill_started', 'backfill_jobs', ['started_at'])
    op.create_index('idx_backfill_job_type', 'backfill_jobs', ['job_type'])


def downgrade() -> None:
    """Drop backfill_jobs table."""
    op.drop_index('idx_backfill_job_type', table_name='backfill_jobs')
    op.drop_index('idx_backfill_started', table_name='backfill_jobs')
    op.drop_index('idx_backfill_status', table_name='backfill_jobs')
    op.drop_table('backfill_jobs')
