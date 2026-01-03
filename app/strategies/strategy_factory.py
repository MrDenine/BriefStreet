"""
Strategy Factory

Factory pattern for creating strategy instances.
"""

from typing import Dict, Type, Optional
from app.strategies.base_strategy import BaseStrategy, StrategyConfig
from app.strategies.buy_the_dip_strategy import BuyTheDipStrategy
from app.strategies.mean_reversion_strategy import MeanReversionStrategy
from app.strategies.momentum_strategy import MomentumStrategy


class StrategyFactory:
    """
    Factory for creating strategy instances.
    
    Usage:
        strategy = StrategyFactory.create("buy_the_dip")
        strategy = StrategyFactory.create("momentum", custom_config)
    """
    
    # Registry of available strategies
    _strategies: Dict[str, Type[BaseStrategy]] = {
        "buy_the_dip": BuyTheDipStrategy,
        "mean_reversion": MeanReversionStrategy,
        "momentum": MomentumStrategy,
    }
    
    @classmethod
    def create(
        cls, 
        strategy_name: str, 
        config: Optional[StrategyConfig] = None
    ) -> BaseStrategy:
        """
        Create a strategy instance.
        
        Args:
            strategy_name: Name of the strategy (e.g., "buy_the_dip")
            config: Optional custom configuration (uses default if None)
            
        Returns:
            Strategy instance
            
        Raises:
            ValueError: If strategy_name is not recognized
        """
        strategy_class = cls._strategies.get(strategy_name.lower())
        
        if not strategy_class:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(
                f"Unknown strategy: '{strategy_name}'. "
                f"Available strategies: {available}"
            )
        
        # Use custom config or default
        if config is None:
            config = strategy_class.get_default_config()
        elif isinstance(config, dict):
            config = StrategyConfig(**config)
        
        return strategy_class(config)
    
    @classmethod
    def get_available_strategies(cls) -> list[str]:
        """
        Get list of available strategy names.
        
        Returns:
            List of strategy names
        """
        return list(cls._strategies.keys())
    
    @classmethod
    def get_strategy_info(cls, strategy_name: str) -> Dict:
        """
        Get default configuration info for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dictionary with strategy information
            
        Raises:
            ValueError: If strategy_name is not recognized
        """
        strategy_class = cls._strategies.get(strategy_name.lower())
        
        if not strategy_class:
            raise ValueError(f"Unknown strategy: '{strategy_name}'")
        
        config = strategy_class.get_default_config()
        return config.model_dump()
    
    @classmethod
    def register_strategy(
        cls, 
        name: str, 
        strategy_class: Type[BaseStrategy]
    ) -> None:
        """
        Register a new strategy (for custom user strategies).
        
        Args:
            name: Strategy name
            strategy_class: Strategy class
        """
        cls._strategies[name.lower()] = strategy_class
