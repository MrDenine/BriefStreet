"""
Portfolio Backtest Service

Service for backtesting portfolios of multiple symbols simultaneously.
Includes correlation analysis and portfolio-level metrics.
"""

import pandas as pd
import numpy as np
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.data_sources.base import DataSourceProvider
from app.strategies.base_strategy import StrategyConfig
from app.services.backtest_service import BacktestService
from app.models.backtest import (
    PortfolioBacktestResult,
    BacktestResult,
    TransactionCosts,
    PositionSizing
)


class PortfolioBacktestService:
    """
    Service for portfolio-level backtesting.
    
    Features:
    - Multiple symbols simultaneously
    - Portfolio-level metrics
    - Correlation analysis
    - Capital allocation
    - Diversification metrics
    """
    
    def __init__(
        self,
        data_provider: DataSourceProvider,
        transaction_costs: Optional[TransactionCosts] = None,
        position_sizing: Optional[PositionSizing] = None
    ):
        self.data_provider = data_provider
        self.transaction_costs = transaction_costs or TransactionCosts()
        self.position_sizing = position_sizing or PositionSizing()
        self.backtest_service = BacktestService(
            data_provider,
            transaction_costs,
            position_sizing
        )
    
    async def run_portfolio_backtest(
        self,
        symbols: List[str],
        strategy_name: str = "buy_the_dip",
        days: int = 365,
        config: Optional[StrategyConfig] = None,
        initial_capital: Optional[float] = None,
        equal_weight: bool = True
    ) -> PortfolioBacktestResult:
        """
        Run backtest for a portfolio of symbols.
        
        Args:
            symbols: List of ticker symbols
            strategy_name: Strategy to use for all symbols
            days: Number of days to backtest
            config: Optional strategy configuration
            initial_capital: Starting capital (distributed across symbols)
            equal_weight: If True, allocate capital equally; else by market cap
            
        Returns:
            PortfolioBacktestResult with portfolio metrics
        """
        capital = initial_capital or self.position_sizing.initial_capital
        
        # Allocate capital per symbol
        capital_per_symbol = capital / len(symbols) if equal_weight else None
        
        # Run backtest for each symbol in parallel
        tasks = []
        for symbol in symbols:
            task = self.backtest_service.run_backtest(
                symbol=symbol,
                strategy_name=strategy_name,
                days=days,
                config=config,
                initial_capital=capital_per_symbol
            )
            tasks.append(task)
        
        # Execute in parallel for speed
        individual_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = {}
        for symbol, result in zip(symbols, individual_results):
            if isinstance(result, BacktestResult):
                valid_results[symbol] = result
            else:
                print(f"⚠️  Skipping {symbol}: {result}")
        
        if not valid_results:
            raise ValueError("No valid backtest results obtained")
        
        # Calculate portfolio metrics
        return self._calculate_portfolio_metrics(
            valid_results,
            strategy_name,
            days,
            capital
        )
    
    def _calculate_portfolio_metrics(
        self,
        individual_results: Dict[str, BacktestResult],
        strategy_name: str,
        days: int,
        initial_capital: float
    ) -> PortfolioBacktestResult:
        """
        Calculate portfolio-level metrics from individual results.
        
        Args:
            individual_results: Dict mapping symbols to their backtest results
            strategy_name: Strategy name
            days: Backtest period
            initial_capital: Initial portfolio capital
            
        Returns:
            PortfolioBacktestResult
        """
        symbols = list(individual_results.keys())
        
        # Aggregate capital
        final_capital = sum(r.final_capital for r in individual_results.values())
        net_profit = final_capital - initial_capital
        total_return = (net_profit / initial_capital) * 100
        
        # Portfolio returns (weighted average)
        returns_list = [r.total_return for r in individual_results.values()]
        weights = [1.0 / len(symbols)] * len(symbols)  # Equal weight
        
        # Calculate portfolio Sharpe ratio (simplified)
        avg_return = np.average(returns_list, weights=weights)
        std_return = np.std(returns_list)
        sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0.0
        
        # Calculate portfolio max drawdown (worst individual drawdown)
        max_drawdown = max(r.max_drawdown for r in individual_results.values())
        
        # Calculate correlation (if we have price data)
        avg_correlation = self._calculate_avg_correlation(individual_results)
        
        # Find best and worst performers
        sorted_by_return = sorted(
            individual_results.items(),
            key=lambda x: x[1].total_return,
            reverse=True
        )
        best_performer = sorted_by_return[0][0] if sorted_by_return else ""
        worst_performer = sorted_by_return[-1][0] if sorted_by_return else ""
        
        return PortfolioBacktestResult(
            symbols=symbols,
            strategy_name=strategy_name,
            period_days=days,
            total_return=round(total_return, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            max_drawdown=round(max_drawdown, 2),
            individual_results=individual_results,
            initial_capital=initial_capital,
            final_capital=round(final_capital, 2),
            net_profit=round(net_profit, 2),
            avg_correlation=round(avg_correlation, 2),
            best_performer=best_performer,
            worst_performer=worst_performer
        )
    
    def _calculate_avg_correlation(
        self,
        individual_results: Dict[str, BacktestResult]
    ) -> float:
        """
        Calculate average correlation between symbols.
        
        This is a simplified version - ideally we'd use actual price data.
        Here we use trade returns as a proxy.
        
        Args:
            individual_results: Individual backtest results
            
        Returns:
            Average pairwise correlation
        """
        if len(individual_results) < 2:
            return 0.0
        
        # Extract returns from each symbol
        returns_matrix = []
        for symbol, result in individual_results.items():
            if result.recent_trades:
                trade_returns = [t.pnl_percent for t in result.recent_trades]
                returns_matrix.append(trade_returns)
        
        if len(returns_matrix) < 2:
            return 0.0
        
        # Make all arrays same length (pad with zeros)
        max_len = max(len(r) for r in returns_matrix)
        padded_returns = []
        for returns in returns_matrix:
            padded = returns + [0] * (max_len - len(returns))
            padded_returns.append(padded)
        
        # Calculate correlation matrix
        try:
            df = pd.DataFrame(padded_returns).T
            corr_matrix = df.corr()
            
            # Get average of off-diagonal elements
            n = len(corr_matrix)
            if n < 2:
                return 0.0
            
            total_corr = corr_matrix.values.sum() - n  # Subtract diagonal
            avg_corr = total_corr / (n * (n - 1))  # Average off-diagonal
            
            return avg_corr
        except:
            return 0.0
    
    async def compare_strategies(
        self,
        symbol: str,
        strategy_names: List[str],
        days: int = 365,
        initial_capital: Optional[float] = None
    ) -> Dict[str, BacktestResult]:
        """
        Compare multiple strategies on the same symbol.
        
        Args:
            symbol: Ticker symbol
            strategy_names: List of strategy names to compare
            days: Backtest period
            initial_capital: Starting capital
            
        Returns:
            Dict mapping strategy names to their results
        """
        tasks = []
        for strategy_name in strategy_names:
            task = self.backtest_service.run_backtest(
                symbol=symbol,
                strategy_name=strategy_name,
                days=days,
                initial_capital=initial_capital
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results
        comparison = {}
        for strategy_name, result in zip(strategy_names, results):
            if isinstance(result, BacktestResult):
                comparison[strategy_name] = result
            else:
                print(f"⚠️  Strategy {strategy_name} failed: {result}")
        
        return comparison
