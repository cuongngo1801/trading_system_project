"""Trading System Package.

A production-grade trading system implementing session-based trend continuation analysis
for forex and indices markets.
"""

__version__ = "0.1.0"
__author__ = "Trading Team"
__description__ = "Production-Grade Session-Based Trend Continuation Trading System"

# Core strategy components (Phase 1 - Available)
from .core.strategy import SessionType, TrendContinuationStrategy, TrendDirection

# Current exports (Phase 1)
__all__ = [
    "SessionType",
    "TrendDirection",
    "TrendContinuationStrategy",
]
