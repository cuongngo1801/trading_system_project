"""Unit tests for the core trading strategy."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from trading_system.core.strategy import (
    SessionType,
    SignalData,
    TrendContinuationStrategy,
    TrendDirection,
)
from trading_system.utils.config import StrategyConfig


class TestTrendContinuationStrategy:
    """Test cases for TrendContinuationStrategy."""

    def test_strategy_initialization(self, strategy_config):
        """Test strategy initialization."""
        strategy = TrendContinuationStrategy(strategy_config)

        assert strategy.config == strategy_config
        assert isinstance(strategy.active_signals, dict)
        assert isinstance(strategy.trend_cache, dict)
        assert len(strategy.active_signals) == 0
        assert len(strategy.trend_cache) == 0

    def test_compute_trend_d1_bullish(self, strategy_config, sample_d1_data):
        """Test D1 trend computation for bullish trend."""
        strategy = TrendContinuationStrategy(strategy_config)

        # Create data with clear bullish trend
        df = sample_d1_data.copy()
        df["close"] = df["close"] * np.linspace(1.0, 1.2, len(df))

        trend = strategy._compute_trend_d1(df)
        assert trend == TrendDirection.BULLISH

    def test_compute_trend_d1_bearish(self, strategy_config, sample_d1_data):
        """Test D1 trend computation for bearish trend."""
        strategy = TrendContinuationStrategy(strategy_config)

        # Create data with clear bearish trend
        df = sample_d1_data.copy()
        df["close"] = df["close"] * np.linspace(1.2, 1.0, len(df))

        trend = strategy._compute_trend_d1(df)
        assert trend == TrendDirection.BEARISH

    def test_compute_trend_d1_insufficient_data(self, strategy_config):
        """Test D1 trend computation with insufficient data."""
        strategy = TrendContinuationStrategy(strategy_config)

        # Create minimal data
        df = pd.DataFrame({"close": [1.1, 1.2, 1.3]})

        trend = strategy._compute_trend_d1(df)
        assert trend == TrendDirection.SIDEWAYS

    def test_calculate_atr(self, strategy_config, sample_h4_data):
        """Test ATR calculation."""
        strategy = TrendContinuationStrategy(strategy_config)

        atr_values = strategy._calculate_atr(sample_h4_data, 14)

        assert isinstance(atr_values, pd.Series)
        assert len(atr_values) == len(sample_h4_data)
        assert not atr_values.isna().all()
        assert all(atr_values >= 0)

    def test_calculate_adx(self, strategy_config, sample_h4_data):
        """Test ADX calculation."""
        strategy = TrendContinuationStrategy(strategy_config)

        adx_values = strategy._calculate_adx(sample_h4_data, 14)

        assert isinstance(adx_values, pd.Series)
        assert len(adx_values) == len(sample_h4_data)
        assert all(adx_values >= 0)
        assert all(adx_values <= 100)

    def test_is_trend_confirmed_true(self, strategy_config):
        """Test trend confirmation when conditions are met."""
        strategy = TrendContinuationStrategy(strategy_config)

        is_confirmed = strategy._is_trend_confirmed(
            TrendDirection.BULLISH, TrendDirection.BULLISH, 30.0  # Above threshold
        )

        assert is_confirmed is True

    def test_is_trend_confirmed_false_misaligned_trends(self, strategy_config):
        """Test trend confirmation when trends are misaligned."""
        strategy = TrendContinuationStrategy(strategy_config)

        is_confirmed = strategy._is_trend_confirmed(
            TrendDirection.BULLISH, TrendDirection.BEARISH, 30.0
        )

        assert is_confirmed is False

    def test_is_trend_confirmed_false_weak_adx(self, strategy_config):
        """Test trend confirmation when ADX is weak."""
        strategy = TrendContinuationStrategy(strategy_config)

        is_confirmed = strategy._is_trend_confirmed(
            TrendDirection.BULLISH, TrendDirection.BULLISH, 20.0  # Below threshold
        )

        assert is_confirmed is False

    def test_create_signal_bullish(self, strategy_config):
        """Test signal creation for bullish trend."""
        strategy = TrendContinuationStrategy(strategy_config)

        signal = strategy._create_signal(
            symbol="EURUSD",
            trend=TrendDirection.BULLISH,
            session=SessionType.US,
            current_price=1.1000,
            atr_value=0.0010,
            adx_strength=30.0,
        )

        assert isinstance(signal, SignalData)
        assert signal.signal_type == "buy"
        assert signal.symbol == "EURUSD"
        assert signal.session == SessionType.US
        assert signal.price == 1.1000
        assert signal.stop_loss < 1.1000  # Stop below entry for buy
        assert signal.take_profit > 1.1000  # Target above entry for buy
        assert 0.0 <= signal.strength <= 1.0

    def test_create_signal_bearish(self, strategy_config):
        """Test signal creation for bearish trend."""
        strategy = TrendContinuationStrategy(strategy_config)

        signal = strategy._create_signal(
            symbol="EURUSD",
            trend=TrendDirection.BEARISH,
            session=SessionType.EUROPEAN,
            current_price=1.1000,
            atr_value=0.0010,
            adx_strength=35.0,
        )

        assert isinstance(signal, SignalData)
        assert signal.signal_type == "sell"
        assert signal.symbol == "EURUSD"
        assert signal.session == SessionType.EUROPEAN
        assert signal.price == 1.1000
        assert signal.stop_loss > 1.1000  # Stop above entry for sell
        assert signal.take_profit < 1.1000  # Target below entry for sell

    @patch("trading_system.core.strategy.datetime")
    def test_generate_signal_confirmed_trend(
        self, mock_datetime, strategy_config, sample_d1_data, sample_h4_data
    ):
        """Test signal generation when trend is confirmed."""
        # Mock datetime.now()
        mock_datetime.now.return_value = datetime(
            2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc
        )

        strategy = TrendContinuationStrategy(strategy_config)

        # Mock analyze_trend to return confirmed trend
        with patch.object(strategy, "analyze_trend") as mock_analyze:
            mock_analyze.return_value = Mock(
                d1_trend=TrendDirection.BULLISH,
                h4_trend=TrendDirection.BULLISH,
                adx_strength=30.0,
                atr_value=0.0010,
                trend_confirmation=True,
            )

            signal = strategy.generate_signal(
                symbol="EURUSD",
                df_d1=sample_d1_data,
                df_h4=sample_h4_data,
                current_session=SessionType.US,
                current_price=1.1000,
            )

            assert signal is not None
            assert signal.signal_type == "buy"
            assert signal.symbol == "EURUSD"

    def test_generate_signal_no_confirmation(
        self, strategy_config, sample_d1_data, sample_h4_data
    ):
        """Test signal generation when trend is not confirmed."""
        strategy = TrendContinuationStrategy(strategy_config)

        # Mock analyze_trend to return unconfirmed trend
        with patch.object(strategy, "analyze_trend") as mock_analyze:
            mock_analyze.return_value = Mock(
                d1_trend=TrendDirection.BULLISH,
                h4_trend=TrendDirection.BEARISH,
                adx_strength=20.0,
                atr_value=0.0010,
                trend_confirmation=False,
            )

            signal = strategy.generate_signal(
                symbol="EURUSD",
                df_d1=sample_d1_data,
                df_h4=sample_h4_data,
                current_session=SessionType.US,
                current_price=1.1000,
            )

            assert signal is None

    def test_get_strategy_status(self, strategy_config):
        """Test strategy status retrieval."""
        strategy = TrendContinuationStrategy(strategy_config)

        status = strategy.get_strategy_status()

        assert isinstance(status, dict)
        assert "name" in status
        assert "active_signals" in status
        assert "cached_analysis" in status
        assert "config" in status
        assert "timestamp" in status
        assert status["name"] == strategy_config.name
        assert status["active_signals"] == 0
        assert status["cached_analysis"] == 0

    def test_analyze_trend_caching(
        self, strategy_config, sample_d1_data, sample_h4_data
    ):
        """Test that trend analysis results are cached."""
        strategy = TrendContinuationStrategy(strategy_config)

        # First analysis
        analysis1 = strategy.analyze_trend(sample_d1_data, sample_h4_data)

        # Manually generate signal to trigger caching
        strategy.generate_signal(
            symbol="EURUSD",
            df_d1=sample_d1_data,
            df_h4=sample_h4_data,
            current_session=SessionType.US,
            current_price=1.1000,
        )

        # Check cache
        assert "EURUSD" in strategy.trend_cache
        cached_analysis = strategy.trend_cache["EURUSD"]
        assert cached_analysis.d1_trend == analysis1.d1_trend
        assert cached_analysis.h4_trend == analysis1.h4_trend
