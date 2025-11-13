"""create alert_configurations and alert_history tables

Revision ID: 005
Revises: 004
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create alert_configurations and alert_history tables with indexes."""
    
    # Create alert_configurations table
    op.create_table(
        'alert_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('service_name', sa.String(length=100), nullable=False),
        sa.Column('metric_type', sa.String(length=100), nullable=False),
        sa.Column('threshold_type', sa.String(length=20), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('comparison_operator', sa.String(length=10), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('evaluation_window_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('notification_channels', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('suppression_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('suppression_start', sa.DateTime(), nullable=True),
        sa.Column('suppression_end', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create indexes for alert_configurations table
    op.create_index('idx_alert_service', 'alert_configurations', ['service_name'])
    op.create_index('idx_alert_enabled', 'alert_configurations', ['enabled'])
    op.create_index('idx_alert_created_by', 'alert_configurations', ['created_by'])
    
    # Create alert_history table
    op.create_table(
        'alert_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notification_channels', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('resolution_method', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['alert_config_id'], ['alert_configurations.id'], ondelete='CASCADE')
    )
    
    # Create indexes for alert_history table
    op.create_index('idx_alert_history_triggered', 'alert_history', ['triggered_at'])
    op.create_index('idx_alert_history_config', 'alert_history', ['alert_config_id'])
    op.create_index('idx_alert_history_resolved', 'alert_history', ['resolved_at'])


def downgrade() -> None:
    """Drop alert_configurations and alert_history tables."""
    
    # Drop alert_history table first (due to foreign key)
    op.drop_index('idx_alert_history_resolved', table_name='alert_history')
    op.drop_index('idx_alert_history_config', table_name='alert_history')
    op.drop_index('idx_alert_history_triggered', table_name='alert_history')
    op.drop_table('alert_history')
    
    # Drop alert_configurations table
    op.drop_index('idx_alert_created_by', table_name='alert_configurations')
    op.drop_index('idx_alert_enabled', table_name='alert_configurations')
    op.drop_index('idx_alert_service', table_name='alert_configurations')
    op.drop_table('alert_configurations')
