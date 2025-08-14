-- PostgreSQL initialization script for Trading System
-- This script creates the main trading database schema

\c trading_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Set default schema
SET search_path = trading, market_data, analytics, monitoring, public;

-- Trading instruments table
CREATE TABLE IF NOT EXISTS trading.instruments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    instrument_type VARCHAR(20) NOT NULL CHECK (instrument_type IN ('forex', 'index', 'commodity', 'crypto')),
    base_currency VARCHAR(3),
    quote_currency VARCHAR(3),
    tick_size DECIMAL(10, 8) NOT NULL,
    pip_value DECIMAL(10, 4) NOT NULL,
    margin_requirement DECIMAL(5, 4) NOT NULL DEFAULT 0.01,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Market data OHLCV table
CREATE TABLE IF NOT EXISTS market_data.ohlcv (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instrument_id UUID NOT NULL REFERENCES trading.instruments(id),
    timeframe VARCHAR(10) NOT NULL CHECK (timeframe IN ('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN1')),
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(12, 6) NOT NULL,
    high_price DECIMAL(12, 6) NOT NULL,
    low_price DECIMAL(12, 6) NOT NULL,
    close_price DECIMAL(12, 6) NOT NULL,
    volume BIGINT NOT NULL DEFAULT 0,
    tick_volume BIGINT NOT NULL DEFAULT 0,
    spread DECIMAL(6, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(instrument_id, timeframe, timestamp_utc)
);

-- Create index for efficient time-series queries
CREATE INDEX IF NOT EXISTS idx_ohlcv_instrument_timeframe_time
    ON market_data.ohlcv (instrument_id, timeframe, timestamp_utc DESC);

-- Trading sessions table
CREATE TABLE trading.trading_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_name VARCHAR(50) NOT NULL UNIQUE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strategy configurations table
CREATE TABLE IF NOT EXISTS trading.strategy_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_name VARCHAR(50) NOT NULL,
    instrument_id UUID NOT NULL REFERENCES trading.instruments(id),
    config_data JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(strategy_name, instrument_id)
);

-- Trading signals table
CREATE TABLE IF NOT EXISTS trading.signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_config_id UUID NOT NULL REFERENCES trading.strategy_configs(id),
    instrument_id UUID NOT NULL REFERENCES trading.instruments(id),
    signal_type VARCHAR(10) NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'CLOSE')),
    signal_strength DECIMAL(3, 2) NOT NULL CHECK (signal_strength BETWEEN 0 AND 1),
    entry_price DECIMAL(12, 6),
    stop_loss DECIMAL(12, 6),
    take_profit DECIMAL(12, 6),
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    session_name VARCHAR(20),
    signal_data JSONB,
    is_executed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient signal queries
CREATE INDEX IF NOT EXISTS idx_signals_instrument_time
    ON trading.signals (instrument_id, timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_signals_unexecuted
    ON trading.signals (is_executed, timestamp_utc DESC) WHERE is_executed = false;

-- Trading orders table
CREATE TABLE IF NOT EXISTS trading.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID REFERENCES trading.signals(id),
    external_order_id VARCHAR(50),
    instrument_id UUID NOT NULL REFERENCES trading.instruments(id),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT')),
    side VARCHAR(4) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity DECIMAL(12, 4) NOT NULL,
    price DECIMAL(12, 6),
    stop_loss DECIMAL(12, 6),
    take_profit DECIMAL(12, 6),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'FILLED', 'PARTIALLY_FILLED', 'CANCELLED', 'REJECTED')),
    filled_quantity DECIMAL(12, 4) NOT NULL DEFAULT 0,
    average_fill_price DECIMAL(12, 6),
    commission DECIMAL(8, 4),
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    filled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Risk management settings
CREATE TABLE IF NOT EXISTS trading.risk_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id VARCHAR(50) NOT NULL,
    max_daily_loss DECIMAL(10, 2) NOT NULL,
    max_positions INTEGER NOT NULL DEFAULT 10,
    max_risk_per_trade DECIMAL(5, 4) NOT NULL DEFAULT 0.02,
    max_correlation DECIMAL(3, 2) NOT NULL DEFAULT 0.7,
    settings_data JSONB,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Account performance tracking
CREATE TABLE IF NOT EXISTS analytics.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date_utc DATE NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    starting_balance DECIMAL(12, 2) NOT NULL,
    ending_balance DECIMAL(12, 2) NOT NULL,
    total_trades INTEGER NOT NULL DEFAULT 0,
    winning_trades INTEGER NOT NULL DEFAULT 0,
    losing_trades INTEGER NOT NULL DEFAULT 0,
    gross_profit DECIMAL(10, 2) NOT NULL DEFAULT 0,
    gross_loss DECIMAL(10, 2) NOT NULL DEFAULT 0,
    commission_paid DECIMAL(8, 2) NOT NULL DEFAULT 0,
    largest_win DECIMAL(10, 2),
    largest_loss DECIMAL(10, 2),
    max_drawdown DECIMAL(10, 2),
    sharpe_ratio DECIMAL(6, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(date_utc, account_id)
);

-- System monitoring logs
CREATE TABLE IF NOT EXISTS monitoring.system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component VARCHAR(50) NOT NULL,
    log_level VARCHAR(10) NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    context_data JSONB,
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for log queries
CREATE INDEX IF NOT EXISTS idx_system_logs_component_time
    ON monitoring.system_logs (component, timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_level_time
    ON monitoring.system_logs (log_level, timestamp_utc DESC);

-- Insert default trading sessions
INSERT INTO trading.trading_sessions (session_name, start_time, end_time, timezone) VALUES
    ('Asian', '00:00:00', '09:00:00', 'Asia/Tokyo'),
    ('European', '07:00:00', '16:00:00', 'Europe/London'),
    ('US', '13:00:00', '22:00:00', 'America/New_York'),
    ('Pacific', '21:00:00', '06:00:00', 'Australia/Sydney')
ON CONFLICT (session_name) DO NOTHING;

-- Insert default instruments
INSERT INTO trading.instruments (symbol, name, instrument_type, base_currency, quote_currency, tick_size, pip_value, margin_requirement) VALUES
    ('US30', 'Dow Jones Industrial Average', 'index', 'USD', 'USD', 0.01, 0.01, 0.005),
    ('XAUUSD', 'Gold vs US Dollar', 'commodity', 'XAU', 'USD', 0.01, 0.01, 0.01),
    ('EURUSD', 'Euro vs US Dollar', 'forex', 'EUR', 'USD', 0.00001, 0.0001, 0.01),
    ('GBPUSD', 'British Pound vs US Dollar', 'forex', 'GBP', 'USD', 0.00001, 0.0001, 0.01),
    ('USDJPY', 'US Dollar vs Japanese Yen', 'forex', 'USD', 'JPY', 0.001, 0.01, 0.01)
ON CONFLICT (symbol) DO NOTHING;

-- Create views for easier querying
CREATE OR REPLACE VIEW trading.active_signals AS
SELECT
    s.*,
    i.symbol,
    i.name as instrument_name,
    sc.strategy_name
FROM trading.signals s
JOIN trading.instruments i ON s.instrument_id = i.id
JOIN trading.strategy_configs sc ON s.strategy_config_id = sc.id
WHERE s.is_executed = false
ORDER BY s.timestamp_utc DESC;

CREATE OR REPLACE VIEW analytics.daily_performance AS
SELECT
    date_utc,
    account_id,
    ending_balance - starting_balance as daily_pnl,
    CASE
        WHEN total_trades > 0 THEN ROUND(winning_trades::decimal / total_trades * 100, 2)
        ELSE 0
    END as win_rate,
    gross_profit + gross_loss as net_profit,
    CASE
        WHEN losing_trades > 0 THEN ROUND(ABS(gross_profit / gross_loss), 2)
        ELSE null
    END as profit_factor
FROM analytics.performance_metrics
ORDER BY date_utc DESC;

-- Grant permissions
GRANT USAGE ON SCHEMA trading TO trading_user;
GRANT USAGE ON SCHEMA market_data TO trading_user;
GRANT USAGE ON SCHEMA analytics TO trading_user;
GRANT USAGE ON SCHEMA monitoring TO trading_user;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA trading TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA market_data TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO trading_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA trading TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA market_data TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA monitoring TO trading_user;

-- Display initialization summary
\echo 'Trading System Database Initialized Successfully!'
\echo 'Schemas created: trading, market_data, analytics, monitoring'
\echo 'Tables created: 9 main tables with proper indexes'
\echo 'Default data inserted: trading sessions and instruments'
\echo 'Views created: active_signals, daily_performance'
