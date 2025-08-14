-- TimescaleDB initialization script for Trading System
-- This script creates hypertables for time-series market data

\c trading_timescale;

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Enable other useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS timeseries;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set default schema
SET search_path = timeseries, analytics, public;

-- Market data tick data (high-frequency)
CREATE TABLE IF NOT EXISTS timeseries.market_ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    bid DECIMAL(12, 6) NOT NULL,
    ask DECIMAL(12, 6) NOT NULL,
    bid_size INTEGER DEFAULT 0,
    ask_size INTEGER DEFAULT 0,
    spread DECIMAL(6, 4) GENERATED ALWAYS AS (ask - bid) STORED,
    mid_price DECIMAL(12, 6) GENERATED ALWAYS AS ((bid + ask) / 2) STORED
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('timeseries.market_ticks', 'time', if_not_exists => TRUE);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_market_ticks_symbol_time
    ON timeseries.market_ticks (symbol, time DESC);

-- OHLCV data (aggregated candles)
CREATE TABLE IF NOT EXISTS timeseries.ohlcv_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open_price DECIMAL(12, 6) NOT NULL,
    high_price DECIMAL(12, 6) NOT NULL,
    low_price DECIMAL(12, 6) NOT NULL,
    close_price DECIMAL(12, 6) NOT NULL,
    volume BIGINT DEFAULT 0,
    tick_volume BIGINT DEFAULT 0,
    spread_avg DECIMAL(6, 4),
    spread_max DECIMAL(6, 4),
    spread_min DECIMAL(6, 4)
);

-- Convert to hypertable
SELECT create_hypertable('timeseries.ohlcv_data', 'time', if_not_exists => TRUE);

-- Create compound index
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timeframe_time
    ON timeseries.ohlcv_data (symbol, timeframe, time DESC);

-- Technical indicators table
CREATE TABLE IF NOT EXISTS timeseries.technical_indicators (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    indicator_value DECIMAL(12, 6),
    indicator_data JSONB,
    PRIMARY KEY (time, symbol, timeframe, indicator_name)
);

-- Convert to hypertable
SELECT create_hypertable('timeseries.technical_indicators', 'time', if_not_exists => TRUE);

-- Strategy signals with timestamps
CREATE TABLE IF NOT EXISTS timeseries.strategy_signals (
    time TIMESTAMPTZ NOT NULL,
    strategy_name VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    signal_type VARCHAR(10) NOT NULL,
    signal_strength DECIMAL(3, 2),
    entry_price DECIMAL(12, 6),
    stop_loss DECIMAL(12, 6),
    take_profit DECIMAL(12, 6),
    signal_data JSONB
);

-- Convert to hypertable
SELECT create_hypertable('timeseries.strategy_signals', 'time', if_not_exists => TRUE);

-- Trading performance metrics (time-series)
CREATE TABLE IF NOT EXISTS analytics.performance_timeseries (
    time TIMESTAMPTZ NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    balance DECIMAL(12, 2) NOT NULL,
    equity DECIMAL(12, 2) NOT NULL,
    margin_used DECIMAL(12, 2) DEFAULT 0,
    margin_free DECIMAL(12, 2) DEFAULT 0,
    drawdown_percent DECIMAL(6, 4),
    open_positions INTEGER DEFAULT 0,
    daily_pnl DECIMAL(10, 2) DEFAULT 0
);

-- Convert to hypertable
SELECT create_hypertable('analytics.performance_timeseries', 'time', if_not_exists => TRUE);

-- System metrics for monitoring
CREATE TABLE IF NOT EXISTS analytics.system_metrics (
    time TIMESTAMPTZ NOT NULL,
    component VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(12, 4),
    metric_unit VARCHAR(20),
    tags JSONB
);

-- Convert to hypertable
SELECT create_hypertable('analytics.system_metrics', 'time', if_not_exists => TRUE);

-- Create continuous aggregates for better performance

-- 1-minute OHLCV from ticks (real-time aggregation)
CREATE MATERIALIZED VIEW IF NOT EXISTS timeseries.ohlcv_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS time,
    symbol,
    FIRST(mid_price, time) AS open_price,
    MAX(mid_price) AS high_price,
    MIN(mid_price) AS low_price,
    LAST(mid_price, time) AS close_price,
    COUNT(*) AS tick_count,
    AVG(spread) AS spread_avg,
    MAX(spread) AS spread_max,
    MIN(spread) AS spread_min
FROM timeseries.market_ticks
GROUP BY time_bucket('1 minute', time), symbol;

-- 5-minute OHLCV aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS timeseries.ohlcv_5m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time) AS time,
    symbol,
    FIRST(open_price, time) AS open_price,
    MAX(high_price) AS high_price,
    MIN(low_price) AS low_price,
    LAST(close_price, time) AS close_price,
    SUM(tick_count) AS total_ticks,
    AVG(spread_avg) AS spread_avg
FROM timeseries.ohlcv_1m
GROUP BY time_bucket('5 minutes', time), symbol;

-- Hourly performance aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.hourly_performance
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS time,
    account_id,
    FIRST(balance, time) AS starting_balance,
    LAST(balance, time) AS ending_balance,
    MAX(equity) AS max_equity,
    MIN(equity) AS min_equity,
    AVG(margin_used) AS avg_margin_used,
    MAX(drawdown_percent) AS max_drawdown,
    AVG(open_positions) AS avg_positions
FROM analytics.performance_timeseries
GROUP BY time_bucket('1 hour', time), account_id;

-- Enable compression for older data (keep recent data uncompressed)
ALTER TABLE timeseries.market_ticks SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'time DESC'
);

ALTER TABLE timeseries.ohlcv_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol, timeframe',
    timescaledb.compress_orderby = 'time DESC'
);

-- Set up compression policies (compress data older than 7 days)
SELECT add_compression_policy('timeseries.market_ticks', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('timeseries.ohlcv_data', INTERVAL '7 days', if_not_exists => TRUE);

-- Set up retention policies (keep data for 1 year)
SELECT add_retention_policy('timeseries.market_ticks', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('analytics.system_metrics', INTERVAL '90 days', if_not_exists => TRUE);

-- Create useful functions for trading analysis

-- Function to calculate ATR (Average True Range)
CREATE OR REPLACE FUNCTION calculate_atr(
    p_symbol VARCHAR(20),
    p_timeframe VARCHAR(10),
    p_period INTEGER DEFAULT 14,
    p_start_time TIMESTAMPTZ DEFAULT NOW() - INTERVAL '1 month'
)
RETURNS TABLE(time TIMESTAMPTZ, atr_value DECIMAL(12, 6)) AS $$
BEGIN
    RETURN QUERY
    WITH true_range AS (
        SELECT
            time,
            GREATEST(
                high_price - low_price,
                ABS(high_price - LAG(close_price) OVER (ORDER BY time)),
                ABS(low_price - LAG(close_price) OVER (ORDER BY time))
            ) AS tr
        FROM timeseries.ohlcv_data
        WHERE symbol = p_symbol
        AND timeframe = p_timeframe
        AND time >= p_start_time
        ORDER BY time
    )
    SELECT
        tr.time,
        AVG(tr.tr) OVER (
            ORDER BY tr.time
            ROWS BETWEEN p_period-1 PRECEDING AND CURRENT ROW
        ) AS atr_value
    FROM true_range tr
    ORDER BY tr.time;
END;
$$ LANGUAGE plpgsql;

-- Function to get latest market data
CREATE OR REPLACE FUNCTION get_latest_ohlcv(
    p_symbol VARCHAR(20),
    p_timeframe VARCHAR(10),
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE(
    time TIMESTAMPTZ,
    open_price DECIMAL(12, 6),
    high_price DECIMAL(12, 6),
    low_price DECIMAL(12, 6),
    close_price DECIMAL(12, 6),
    volume BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.time,
        o.open_price,
        o.high_price,
        o.low_price,
        o.close_price,
        o.volume
    FROM timeseries.ohlcv_data o
    WHERE o.symbol = p_symbol
    AND o.timeframe = p_timeframe
    ORDER BY o.time DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Create user and grant permissions
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'timescale_user') THEN
        CREATE ROLE timescale_user WITH LOGIN PASSWORD 'timescale_password';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA timeseries TO timescale_user;
GRANT USAGE ON SCHEMA analytics TO timescale_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA timeseries TO timescale_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO timescale_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA timeseries TO timescale_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO timescale_user;

-- Enable refresh policies for continuous aggregates
SELECT add_continuous_aggregate_policy('timeseries.ohlcv_1m',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('timeseries.ohlcv_5m',
    start_offset => INTERVAL '4 hours',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE);

-- Display initialization summary
\echo 'TimescaleDB Trading System Initialized Successfully!'
\echo 'Hypertables created: market_ticks, ohlcv_data, technical_indicators, strategy_signals'
\echo 'Continuous aggregates: ohlcv_1m, ohlcv_5m, hourly_performance'
\echo 'Compression enabled: 7-day policy for efficient storage'
\echo 'Retention policies: 1 year for ticks, 90 days for system metrics'
\echo 'Custom functions: calculate_atr, get_latest_ohlcv'
