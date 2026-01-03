"""
Trading Strategy Module

This module provides a flexible strategy pattern for backtesting different trading strategies.
"""

from app.strategies.base_strategy import BaseStrategy, StrategyConfig
from app.strategies.buy_the_dip_strategy import BuyTheDipStrategy
from app.strategies.mean_reversion_strategy import MeanReversionStrategy
from app.strategies.momentum_strategy import MomentumStrategy
from app.strategies.strategy_factory import StrategyFactory

__all__ = [
    "BaseStrategy",
    "StrategyConfig",
    "BuyTheDipStrategy",
    "MeanReversionStrategy",
    "MomentumStrategy",
    "StrategyFactory",
]
