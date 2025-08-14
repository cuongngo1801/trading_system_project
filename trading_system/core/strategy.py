"""
Core trading strategy implementation for session-based trend continuation.

This module implements the main trading strategy that analyzes trend continuation
across different market sessions using EMA crossovers and ADX filters.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from trading_system.utils.config import StrategyConfig
from trading_system.utils.logger import get_logger, get_performance_logger


class TrendDirection(Enum):
    """Trend direction enumeration."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"


class SessionType(Enum):
    """Trading session types."""

    ASIAN = "asian"
    EUROPEAN = "european"
    US = "us"
    OVERLAP = "overlap"


@dataclass
class SignalData:
    """Trading signal data structure."""

    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    strength: float  # 0.0 to 1.0
    session: SessionType
    timestamp: datetime
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_amount: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TrendAnalysis:
    """Trend analysis results."""

    d1_trend: TrendDirection
    h4_trend: TrendDirection
    adx_strength: float
    ema_fast: float
    ema_slow: float
    atr_value: float
    trend_confirmation: bool


class TrendContinuationStrategy:
    """
    Production-grade trend continuation strategy implementing session-based analysis.

    Strategy Logic:
    1. Daily (D1) trend identification using EMA crossover (50/200)
    2. H4 trend confirmation using shorter EMAs (20/50)
    3. ADX filter for trend strength (> 25)
    4. Session-based entry timing
    5. ATR-based risk management
    """

    def __init__(self, config: StrategyConfig):
        """Initialize strategy with configuration.

        Args:
            config: Strategy configuration parameters
        """
        self.config = config
        self.logger = get_logger("strategy", {"component": "trend_continuation"})
        self.perf_logger = get_performance_logger("strategy_performance")

        # Strategy state
        self.active_signals: Dict[str, SignalData] = {}
        self.trend_cache: Dict[str, TrendAnalysis] = {}

        self.logger.info("TrendContinuationStrategy initialized", config=config.dict())

    def analyze_trend(self, df_d1: pd.DataFrame, df_h4: pd.DataFrame) -> TrendAnalysis:
        """Analyze trend using D1 and H4 timeframes.

        Args:
            df_d1: Daily timeframe data
            df_h4: H4 timeframe data

        Returns:
            TrendAnalysis object with trend information
        """
        try:
            # Calculate D1 trend
            d1_trend = self._compute_trend_d1(df_d1)

            # Calculate H4 trend and indicators
            (
                h4_trend,
                adx_strength,
                ema_fast,
                ema_slow,
                atr_value,
            ) = self._compute_trend_h4(df_h4)

            # Determine trend confirmation
            trend_confirmation = self._is_trend_confirmed(
                d1_trend, h4_trend, adx_strength
            )

            analysis = TrendAnalysis(
                d1_trend=d1_trend,
                h4_trend=h4_trend,
                adx_strength=adx_strength,
                ema_fast=ema_fast,
                ema_slow=ema_slow,
                atr_value=atr_value,
                trend_confirmation=trend_confirmation,
            )

            self.logger.debug(
                "Trend analysis completed",
                d1_trend=d1_trend.value,
                h4_trend=h4_trend.value,
                adx_strength=adx_strength,
                trend_confirmation=trend_confirmation,
            )

            return analysis

        except Exception as e:
            self.logger.exception("Error in trend analysis", error=str(e))
            raise

    def _compute_trend_d1(self, df_d1: pd.DataFrame) -> TrendDirection:
        """Compute D1 trend using EMA crossover.

        Args:
            df_d1: Daily timeframe data

        Returns:
            Trend direction
        """
        if len(df_d1) < max(self.config.d1_ema_fast, self.config.d1_ema_slow):
            return TrendDirection.SIDEWAYS

        # Calculate EMAs
        ema_fast = df_d1["close"].ewm(span=self.config.d1_ema_fast).mean()
        ema_slow = df_d1["close"].ewm(span=self.config.d1_ema_slow).mean()

        # Get latest values
        latest_fast = ema_fast.iloc[-1]
        latest_slow = ema_slow.iloc[-1]

        # Determine trend
        if latest_fast > latest_slow:
            return TrendDirection.BULLISH
        elif latest_fast < latest_slow:
            return TrendDirection.BEARISH
        else:
            return TrendDirection.SIDEWAYS

    def _compute_trend_h4(
        self, df_h4: pd.DataFrame
    ) -> Tuple[TrendDirection, float, float, float, float]:
        """Compute H4 trend and technical indicators.

        Args:
            df_h4: H4 timeframe data

        Returns:
            Tuple of (trend, adx_strength, ema_fast, ema_slow, atr_value)
        """
        if len(df_h4) < max(
            self.config.h4_ema_fast, self.config.h4_ema_slow, self.config.adx_period
        ):
            return TrendDirection.SIDEWAYS, 0.0, 0.0, 0.0, 0.0

        # Calculate EMAs
        ema_fast = df_h4["close"].ewm(span=self.config.h4_ema_fast).mean()
        ema_slow = df_h4["close"].ewm(span=self.config.h4_ema_slow).mean()

        # Calculate ADX
        adx_value = self._calculate_adx(df_h4, self.config.adx_period)

        # Calculate ATR
        atr_value = self._calculate_atr(df_h4, self.config.atr_period)

        # Get latest values
        latest_fast = ema_fast.iloc[-1]
        latest_slow = ema_slow.iloc[-1]
        latest_adx = adx_value.iloc[-1] if len(adx_value) > 0 else 0.0
        latest_atr = atr_value.iloc[-1] if len(atr_value) > 0 else 0.0

        # Determine H4 trend
        if latest_fast > latest_slow:
            h4_trend = TrendDirection.BULLISH
        elif latest_fast < latest_slow:
            h4_trend = TrendDirection.BEARISH
        else:
            h4_trend = TrendDirection.SIDEWAYS

        return h4_trend, latest_adx, latest_fast, latest_slow, latest_atr

    def _calculate_adx(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average Directional Index (ADX).

        Args:
            df: OHLC data
            period: ADX period

        Returns:
            ADX values
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Calculate True Range (TR)
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate Directional Movement
        dm_plus = high.diff()
        dm_minus = -low.diff()

        # Set DM to 0 if not the strongest move
        dm_plus[dm_plus < dm_minus] = 0
        dm_plus[dm_plus < 0] = 0
        dm_minus[dm_minus < dm_plus] = 0
        dm_minus[dm_minus < 0] = 0

        # Calculate smoothed averages
        atr = tr.rolling(window=period).mean()
        di_plus = (dm_plus.rolling(window=period).mean() / atr) * 100
        di_minus = (dm_minus.rolling(window=period).mean() / atr) * 100

        # Calculate ADX
        dx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100
        adx = dx.rolling(window=period).mean()

        return adx.fillna(0)

    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range (ATR).

        Args:
            df: OHLC data
            period: ATR period

        Returns:
            ATR values
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Calculate True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        # True Range is the maximum of the three
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR as exponential moving average of TR
        atr = tr.ewm(span=period).mean()

        return atr.fillna(0)

    def _is_trend_confirmed(
        self, d1_trend: TrendDirection, h4_trend: TrendDirection, adx_strength: float
    ) -> bool:
        """Check if trend is confirmed across timeframes.

        Args:
            d1_trend: Daily trend direction
            h4_trend: H4 trend direction
            adx_strength: ADX strength value

        Returns:
            True if trend is confirmed
        """
        # Trends must align and ADX must be above threshold
        trends_align = d1_trend == h4_trend and d1_trend != TrendDirection.SIDEWAYS

        adx_confirms = adx_strength >= self.config.adx_threshold

        return trends_align and adx_confirms

    def generate_signal(
        self,
        symbol: str,
        df_d1: pd.DataFrame,
        df_h4: pd.DataFrame,
        current_session: SessionType,
        current_price: float,
    ) -> Optional[SignalData]:
        """Generate trading signal based on trend analysis.

        Args:
            symbol: Trading symbol
            df_d1: Daily timeframe data
            df_h4: H4 timeframe data
            current_session: Current trading session
            current_price: Current market price

        Returns:
            SignalData if signal generated, None otherwise
        """
        try:
            start_time = datetime.now()

            # Perform trend analysis
            analysis = self.analyze_trend(df_d1, df_h4)

            # Cache analysis
            self.trend_cache[symbol] = analysis

            # Generate signal if trend is confirmed
            signal = None
            if analysis.trend_confirmation:
                signal = self._create_signal(
                    symbol=symbol,
                    trend=analysis.d1_trend,
                    session=current_session,
                    current_price=current_price,
                    atr_value=analysis.atr_value,
                    adx_strength=analysis.adx_strength,
                )

            # Log performance
            duration = (datetime.now() - start_time).total_seconds()
            self.perf_logger.log_signal_generation(
                symbol=symbol,
                signal_type=signal.signal_type if signal else "hold",
                strength=signal.strength if signal else 0.0,
                generation_time=duration,
            )

            return signal

        except Exception as e:
            self.logger.exception(
                "Error generating signal",
                symbol=symbol,
                session=current_session.value,
                error=str(e),
            )
            return None

    def _create_signal(
        self,
        symbol: str,
        trend: TrendDirection,
        session: SessionType,
        current_price: float,
        atr_value: float,
        adx_strength: float,
    ) -> SignalData:
        """Create trading signal with risk management parameters.

        Args:
            symbol: Trading symbol
            trend: Confirmed trend direction
            session: Current session
            current_price: Current price
            atr_value: ATR value for risk calculation
            adx_strength: ADX strength

        Returns:
            SignalData object
        """
        # Determine signal type
        signal_type = "buy" if trend == TrendDirection.BULLISH else "sell"

        # Calculate signal strength (normalized ADX)
        strength = min(adx_strength / 50.0, 1.0)  # Normalize to 0-1

        # Calculate stop loss and take profit using ATR
        atr_multiplier = self.config.atr_multiplier

        if trend == TrendDirection.BULLISH:
            stop_loss = current_price - (atr_value * atr_multiplier)
            take_profit = current_price + (atr_value * atr_multiplier * 2)
        else:
            stop_loss = current_price + (atr_value * atr_multiplier)
            take_profit = current_price - (atr_value * atr_multiplier * 2)

        # Create signal
        signal = SignalData(
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            session=session,
            timestamp=datetime.now(timezone.utc),
            price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={
                "atr_value": atr_value,
                "adx_strength": adx_strength,
                "trend_d1": trend.value,
                "atr_multiplier": atr_multiplier,
            },
        )

        self.logger.info(
            f"Signal generated: {signal_type} {symbol}",
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            session=session.value,
            price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        return signal

    def update_signal(
        self, symbol: str, signal_id: str, market_data: Dict[str, Any]
    ) -> Optional[SignalData]:
        """Update existing signal based on new market data.

        Args:
            symbol: Trading symbol
            signal_id: Signal identifier
            market_data: Updated market data

        Returns:
            Updated signal or None if signal should be closed
        """
        # TODO: Implement signal update logic
        # This would handle:
        # - Trailing stops
        # - Signal strength updates
        # - Exit conditions
        pass

    def get_strategy_status(self) -> Dict[str, Any]:
        """Get current strategy status and metrics.

        Returns:
            Strategy status dictionary
        """
        return {
            "name": self.config.name,
            "active_signals": len(self.active_signals),
            "cached_analysis": len(self.trend_cache),
            "config": self.config.dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
