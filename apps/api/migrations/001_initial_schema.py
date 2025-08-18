"""Initial database schema migration

Revision ID: 001
Revises: 
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    
    # Users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False, server_default='learner'),
        sa.Column('subscription_status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Backtests table
    op.create_table('backtests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('strategy', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('initial_capital', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_return', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('sharpe_ratio', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('max_drawdown', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Trades table
    op.create_table('trades',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('backtest_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=8), nullable=False),
        sa.Column('price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('trade_type', sa.String(length=20), nullable=False, server_default='paper'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='executed'),
        sa.ForeignKeyConstraint(['backtest_id'], ['backtests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # User progress table
    op.create_table('user_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lessons_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('paper_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('backtests_run', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('badges_earned', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('tier', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_subscription_id')
    )
    
    # API keys table
    op.create_table('api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Audit logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_tier', 'users', ['tier'])
    op.create_index('idx_backtests_user_id', 'backtests', ['user_id'])
    op.create_index('idx_backtests_symbol', 'backtests', ['symbol'])
    op.create_index('idx_backtests_created_at', 'backtests', ['created_at'])
    op.create_index('idx_trades_user_id', 'trades', ['user_id'])
    op.create_index('idx_trades_backtest_id', 'trades', ['backtest_id'])
    op.create_index('idx_trades_timestamp', 'trades', ['timestamp'])
    op.create_index('idx_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    
    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers
    op.execute("""
        CREATE TRIGGER update_users_updated_at 
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_subscriptions_updated_at 
        BEFORE UPDATE ON subscriptions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Insert default admin user (password: admin123)
    op.execute("""
        INSERT INTO users (email, password_hash, tier) VALUES 
        ('admin@aimarketterminal.com', crypt('admin123', gen_salt('bf')), 'enterprise');
    """)
    
    # Create views for analytics
    op.execute("""
        CREATE VIEW user_analytics AS
        SELECT 
            u.id,
            u.email,
            u.tier,
            u.subscription_status,
            u.created_at,
            COUNT(b.id) as total_backtests,
            COUNT(t.id) as total_trades,
            COALESCE(SUM(CASE WHEN t.side = 'buy' THEN t.quantity * t.price ELSE 0 END), 0) as total_volume,
            up.lessons_completed,
            up.paper_trades,
            up.current_streak
        FROM users u
        LEFT JOIN backtests b ON u.id = b.user_id
        LEFT JOIN trades t ON u.id = t.user_id
        LEFT JOIN user_progress up ON u.id = up.user_id
        GROUP BY u.id, u.email, u.tier, u.subscription_status, u.created_at, up.lessons_completed, up.paper_trades, up.current_streak;
    """)
    
    op.execute("""
        CREATE VIEW backtest_performance AS
        SELECT 
            b.id,
            b.symbol,
            b.strategy,
            b.total_return,
            b.sharpe_ratio,
            b.max_drawdown,
            b.status,
            b.created_at,
            u.email as user_email,
            u.tier as user_tier
        FROM backtests b
        JOIN users u ON b.user_id = u.id
        WHERE b.status = 'completed';
    """)
    
    # Create read-only reporting user
    op.execute("""
        CREATE USER reporting_user WITH PASSWORD 'reporting_password_2024';
        GRANT CONNECT ON DATABASE ai_market_terminal TO reporting_user;
        GRANT USAGE ON SCHEMA public TO reporting_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO reporting_user;
        GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO reporting_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO reporting_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO reporting_user;
    """)


def downgrade():
    # Drop views
    op.execute('DROP VIEW IF EXISTS backtest_performance')
    op.execute('DROP VIEW IF EXISTS user_analytics')
    
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions')
    op.execute('DROP TRIGGER IF EXISTS update_users_updated_at ON users')
    
    # Drop function
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop reporting user
    op.execute('DROP USER IF EXISTS reporting_user')
    
    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('api_keys')
    op.drop_table('subscriptions')
    op.drop_table('user_progress')
    op.drop_table('trades')
    op.drop_table('backtests')
    op.drop_table('users')
