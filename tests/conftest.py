"""Test configuration and fixtures."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from trading_system.utils.config import StrategyConfig


@pytest.fixture
def strategy_config():
    """Create test strategy configuration."""
    return StrategyConfig(
        name="TestStrategy",
        d1_ema_fast=50,
        d1_ema_slow=200,
        h4_ema_fast=20,
        h4_ema_slow=50,
        adx_period=14,
        adx_threshold=25.0,
        atr_period=14,
        atr_multiplier=2.0,
    )


@pytest.fixture
def sample_ohlc_data():
    """Create sample OHLC data for testing."""
    dates = pd.date_range(
        start="2023-01-01", periods=5000, freq="H"
    )  # Increased from 300

    # Generate sample price data with trend
    np.random.seed(42)
    prices = []
    base_price = 1.1000

    for i in range(len(dates)):
        # Add slight upward trend with noise
        trend = i * 0.0001
        noise = np.random.normal(0, 0.0005)
        price = base_price + trend + noise
        prices.append(price)

    # Create OHLC data
    data = []
    for i, price in enumerate(prices):
        spread = np.random.uniform(0.0001, 0.0005)
        high = price + spread / 2
        low = price - spread / 2
        open_price = prices[i - 1] if i > 0 else price
        close = price

        data.append(
            {
                "timestamp": dates[i],
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": np.random.randint(100, 1000),
            }
        )

    df = pd.DataFrame(data)
    df.set_index("timestamp", inplace=True)
    return df


@pytest.fixture
def sample_d1_data(sample_ohlc_data):
    """Create sample daily data."""
    return (
        sample_ohlc_data.resample("D")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna()
    )


@pytest.fixture
def sample_h4_data(sample_ohlc_data):
    """Create sample H4 data."""
    return (
        sample_ohlc_data.resample("4H")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna()
    )


@pytest.fixture
def mock_database_config():
    """Create mock database configuration."""
    return {
        "url": "sqlite:///:memory:",
        "pool_size": 1,
        "max_overflow": 1,
        "pool_timeout": 30,
    }


@pytest.fixture
def mock_kafka_config():
    """Create mock Kafka configuration."""
    return {
        "bootstrap_servers": "localhost:9092",
        "group_id": "test-group",
        "auto_offset_reset": "earliest",
        "enable_auto_commit": True,
        "session_timeout_ms": 30000,
        "request_timeout_ms": 40000,
    }


@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    return {
        "symbol": "EURUSD",
        "bid": 1.1000,
        "ask": 1.1002,
        "timestamp": datetime.utcnow(),
        "volume": 1000,
    }
