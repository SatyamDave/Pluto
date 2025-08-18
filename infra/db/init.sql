-- AI Market Terminal Database Initialization
-- This script sets up the initial database schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tier VARCHAR(50) DEFAULT 'learner' CHECK (tier IN ('learner', 'pro', 'quant', 'enterprise')),
    subscription_status VARCHAR(50) DEFAULT 'active' CHECK (subscription_status IN ('active', 'inactive', 'cancelled', 'past_due')),
    stripe_customer_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Backtests table
CREATE TABLE backtests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    strategy VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15,2) NOT NULL,
    total_return DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    parameters JSONB,
    results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Trades table
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    backtest_id UUID REFERENCES backtests(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    trade_type VARCHAR(20) DEFAULT 'paper' CHECK (trade_type IN ('paper', 'live')),
    status VARCHAR(20) DEFAULT 'executed' CHECK (status IN ('pending', 'executed', 'cancelled', 'failed'))
);

-- User progress table
CREATE TABLE user_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lessons_completed INTEGER DEFAULT 0,
    paper_trades INTEGER DEFAULT 0,
    backtests_run INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    badges_earned TEXT[],
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    tier VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    permissions JSONB,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(tier);
CREATE INDEX idx_backtests_user_id ON backtests(user_id);
CREATE INDEX idx_backtests_symbol ON backtests(symbol);
CREATE INDEX idx_backtests_created_at ON backtests(created_at);
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_backtest_id ON trades(backtest_id);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: admin123)
INSERT INTO users (email, password_hash, tier) VALUES 
('admin@aimarketterminal.com', crypt('admin123', gen_salt('bf')), 'enterprise');

-- Create views for analytics
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

-- Create view for backtest performance
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
