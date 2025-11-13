"""create insight_feedback table

Revision ID: 002
Revises: 001
Create Date: 2024-01-08 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create insight_feedback table with indexes and unique constraint."""
    op.create_table(
        'insight_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('insight_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('flag_type', sa.String(length=50), nullable=True),
        sa.Column('flag_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_feedback_insight', 'insight_feedback', ['insight_id'])
    op.create_index('idx_feedback_user', 'insight_feedback', ['user_id'])
    op.create_index('idx_feedback_created', 'insight_feedback', ['created_at'])
    
    # Create unique constraint to ensure one feedback per user per insight
    op.create_unique_constraint(
        'uq_insight_user_feedback',
        'insight_feedback',
        ['insight_id', 'user_id']
    )


def downgrade() -> None:
    """Drop insight_feedback table."""
    op.drop_constraint('uq_insight_user_feedback', 'insight_feedback', type_='unique')
    op.drop_index('idx_feedback_created', table_name='insight_feedback')
    op.drop_index('idx_feedback_user', table_name='insight_feedback')
    op.drop_index('idx_feedback_insight', table_name='insight_feedback')
    op.drop_table('insight_feedback')
