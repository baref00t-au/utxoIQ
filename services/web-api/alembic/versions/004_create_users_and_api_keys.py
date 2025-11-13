"""create users and api_keys tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users and api_keys tables with indexes."""
    # Drop existing tables if they exist (from previous incomplete setup)
    op.execute("DROP TABLE IF EXISTS api_keys CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('firebase_uid', sa.String(length=128), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('subscription_tier', sa.String(length=20), nullable=False, server_default='free'),
        sa.Column('stripe_customer_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('firebase_uid'),
        sa.UniqueConstraint('email')
    )
    
    # Create indexes for users table
    op.create_index('idx_user_firebase_uid', 'users', ['firebase_uid'])
    op.create_index('idx_user_email', 'users', ['email'])
    
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('key_prefix', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('key_hash')
    )
    
    # Create indexes for api_keys table
    op.create_index('idx_apikey_hash', 'api_keys', ['key_hash'])
    op.create_index('idx_apikey_user', 'api_keys', ['user_id'])


def downgrade() -> None:
    """Drop users and api_keys tables."""
    # Drop api_keys table first (due to foreign key)
    op.drop_index('idx_apikey_user', table_name='api_keys')
    op.drop_index('idx_apikey_hash', table_name='api_keys')
    op.drop_table('api_keys')
    
    # Drop users table
    op.drop_index('idx_user_email', table_name='users')
    op.drop_index('idx_user_firebase_uid', table_name='users')
    op.drop_table('users')
