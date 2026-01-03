"""
Backtest Service

Service for running backtests with different trading strategies.
Uses Strategy Pattern for flexibility with realistic simulation.

Features:
- Transaction costs (commission + slippage)
- Position sizing
- Portfolio capital tracking
- Realistic constraints
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.data_sources.base import DataSourceProvider
from app.strategies.base_strategy import BaseStrategy
from app.strategies.strategy_factory import StrategyFactory
from app.models.backtest import (
    BacktestResult, 
    TradeRecord, 
    TransactionCosts, 
    PositionSizing
)


class BacktestService:
    """
    Service for backtesting trading strategies with realistic simulation.
    
    Features:
    - Strategy Pattern support
    - Transaction costs (commission + slippage)
    - Position sizing
    - Stop Loss / Take Profit
    - Capital tracking
    - Detailed trade records
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
    
    async def run_backtest(
        self,
        symbol: str,
        strategy_name: str,
        interval: str = "1d",
        days: int = 365,
        limit_history_days: int = 200,
        config: Optional[Dict[str, Any]] = None,
        initial_capital: Optional[float] = None
    ) -> BacktestResult:
        """
        Run realistic backtest with transaction costs and position sizing.
        
        Args:
            symbol: Stock/crypto ticker symbol
            strategy_name: Name of the strategy to use
            days: Number of days to backtest
            config: Optional custom strategy configuration
            initial_capital: Starting capital (uses default if None)
            
        Returns:
            BacktestResult with comprehensive metrics
            
        Raises:
            ValueError: If no data available or invalid strategy
        """
        # 1. Get historical data
        # Extra buffer for indicator warm-up (e.g., EMA 200 needs 200+ days)
        candles = await self.data_provider.get_historical_prices(
            symbol, 
            interval=interval, 
            limit=days + limit_history_days
        )
        
        if not candles:
            raise ValueError(f"No historical data found for {symbol}")
        
        # 2. Prepare DataFrame
        df = pd.DataFrame([c.model_dump() for c in candles])
        df.set_index('timestamp', inplace=True)
        
        # 3. Create strategy instance
        strategy = StrategyFactory.create(strategy_name, config)
        
        # 4. Prepare data with strategy
        df = strategy.prepare_data(df)
        
        # Trim to requested period to ensure consistent backtest duration
        # This prevents "Variable Period Bias" where strategies with different 
        # indicator warm-up periods are tested on different time windows.
        if len(df) > days:
            df = df.iloc[-days:]
        
        # 5. Set initial capital
        capital = initial_capital or self.position_sizing.initial_capital
        
        # 6. Run realistic simulation with capital tracking
        trades, final_capital = self._simulate_trades_realistic(df, strategy, capital)
        
        # 7. Calculate buy & hold for comparison
        buy_hold_return = self._calculate_buy_hold(df, days)
        
        # 8. Calculate comprehensive metrics
        result_metrics = self._calculate_metrics_realistic(
            symbol, days, trades, strategy, capital, final_capital, buy_hold_return, df
        )

        return result_metrics
    
    def _simulate_trades_realistic(
        self, 
        df: pd.DataFrame, 
        strategy: BaseStrategy,
        initial_capital: float
    ) -> tuple[List[Dict[str, Any]], float]:
        """
        Simulate trades with realistic capital tracking and transaction costs.
        Refactored to use Time-Step Loop to avoid look-ahead bias.
        
        Args:
            df: DataFrame with signals
            strategy: Strategy instance
            initial_capital: Starting capital
            
        Returns:
            Tuple of (trades list, final capital)
        """
        trades = []
        current_capital = initial_capital
        active_position = None
        
        # Iterate through each day
        for i in range(len(df)):
            current_date = df.index[i]
            current_row = df.iloc[i]
            
            # 1. Check Entry Conditions (if no active position)
            # We look at YESTERDAY's signal to enter TODAY at Open
            if active_position is None and i > 0:
                prev_row = df.iloc[i-1]
                
                if prev_row['Signal'] == True:
                    # Entry at Current Open
                    entry_price = current_row['open']
                    
                    # Position Sizing
                    shares = self.position_sizing.calculate_position_size(
                        current_capital, 
                        entry_price
                    )
                    
                    if shares > 0:
                        entry_value = shares * entry_price
                        entry_costs = self.transaction_costs.calculate_costs(entry_value)
                        
                        # Check Capital Sufficiency
                        if entry_value + entry_costs <= current_capital:
                            current_capital -= (entry_value + entry_costs)
                            
                            active_position = {
                                "entry_date": current_date,
                                "entry_price": entry_price,
                                "shares": shares,
                                "entry_costs": entry_costs,
                                "entry_idx": i
                            }

            # 2. Check Exit Conditions (if we have an active position)
            # This runs for both existing positions AND positions just entered today (Intraday Exit)
            if active_position:
                entry_price = active_position['entry_price']
                days_held = i - active_position['entry_idx']
                
                # Check Strategy Exit (SL/TP) using High/Low of current day
                should_exit, reason = strategy.check_exit_conditions(
                    entry_price,
                    current_row['close'],
                    current_low=current_row['low'],
                    current_high=current_row['high']
                )
                
                # Check Time-based Exit
                if not should_exit and days_held >= strategy.config.holding_days:
                    should_exit = True
                    reason = "TIME_BASED"
                
                # Force exit on last day of data
                if i == len(df) - 1 and not should_exit:
                    should_exit = True
                    reason = "END_OF_DATA"
                
                if should_exit:
                    # Determine Exit Price
                    exit_price = current_row['close'] # Default
                    
                    if reason == "STOP_LOSS":
                        sl_price = entry_price * (1 - strategy.config.stop_loss_pct / 100)
                        # Check for gap down: if Open < SL, we exit at Open
                        if current_row['open'] < sl_price:
                            exit_price = current_row['open']
                        else:
                            exit_price = sl_price
                            
                    elif reason == "TAKE_PROFIT":
                        tp_price = entry_price * (1 + strategy.config.take_profit_pct / 100)
                        # Check for gap up: if Open > TP, we exit at Open
                        if current_row['open'] > tp_price:
                            exit_price = current_row['open']
                        else:
                            exit_price = tp_price
                    
                    # Execute Exit
                    shares = active_position['shares']
                    exit_value = shares * exit_price
                    exit_costs = self.transaction_costs.calculate_costs(exit_value)
                    
                    current_capital += (exit_value - exit_costs)
                    
                    # Calculate Metrics
                    gross_pnl = (exit_price - entry_price) * shares
                    total_costs = active_position['entry_costs'] + exit_costs
                    net_pnl = gross_pnl - total_costs
                    net_pnl_percent = (net_pnl / (shares * entry_price)) * 100
                    
                    trades.append({
                        "entry_date": active_position['entry_date'],
                        "entry_price": entry_price,
                        "exit_date": current_date,
                        "exit_price": exit_price,
                        "shares": shares,
                        "gross_pnl": gross_pnl,
                        "transaction_costs": total_costs,
                        "net_pnl": net_pnl,
                        "pnl_percent": net_pnl_percent,
                        "win": net_pnl > 0,
                        "exit_reason": reason
                    })
                    
                    active_position = None
                    # Continue to next day

        return trades, current_capital
    
    def _calculate_buy_hold(self, df: pd.DataFrame, days: int) -> float:
        """Calculate buy and hold return for comparison."""
        if len(df) < 2:
            return 0.0
        
        # Use only the last 'days' period for fair comparison
        actual_start_idx = max(0, len(df) - days)
        start_price = df.iloc[actual_start_idx]['close']
        end_price = df.iloc[-1]['close']
        return ((end_price - start_price) / start_price) * 100
    
    def _calculate_metrics_realistic(
        self,
        symbol: str,
        days: int,
        trades: List[Dict[str, Any]],
        strategy: BaseStrategy,
        initial_capital: float,
        final_capital: float,
        buy_hold_return: float,
        df: pd.DataFrame
    ) -> BacktestResult:
        """
        Calculate comprehensive backtest metrics with realistic costs.
        
        Args:
            symbol: Trading symbol
            days: Backtest period
            trades: List of trade records
            strategy: Strategy instance
            initial_capital: Starting capital
            final_capital: Ending capital
            buy_hold_return: Buy & hold return for comparison
            df: Price data DataFrame
            
        Returns:
            BacktestResult with all metrics
        """
        # Prepare chart data
        price_data = [
            {
                "timestamp": str(idx),
                "open": row['open'],
                "high": row['high'],
                "low": row['low'],
                "close": row['close'],
                "volume": row.get('volume', 0),
                "signal": bool(row.get('Signal', False))
            }
            for idx, row in df.iterrows()
        ]

        if not trades:
            # Calculate actual start date based on requested period
            actual_start_idx = max(0, len(df) - days) if len(df) > 0 else 0
            return BacktestResult(
                symbol=symbol,
                strategy_name=strategy.name,
                strategy_config=strategy.config.model_dump(),
                period_days=days,
                start_date=df.index[actual_start_idx] if len(df) > 0 else None,
                end_date=df.index[-1] if len(df) > 0 else None,
                total_trades=0,
                win_rate=0.0,
                avg_return=0.0,
                best_trade=0.0,
                worst_trade=0.0,
                total_return=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_duration=0,
                profit_factor=0.0,
                expectancy=0.0,
                total_transaction_costs=0.0,
                avg_cost_per_trade=0.0,
                initial_capital=initial_capital,
                final_capital=initial_capital,
                net_profit=0.0,
                recent_trades=[],
                price_data=price_data,
                trade_markers=[],
                buy_and_hold_return=buy_hold_return,
                alpha=0.0
            )
        
        df_trades = pd.DataFrame(trades)
        
        # Basic metrics
        total_trades = len(trades)
        wins = df_trades['win'].sum()
        win_rate = (wins / total_trades) * 100
        avg_return = df_trades['pnl_percent'].mean()
        best_trade = df_trades['pnl_percent'].max()
        worst_trade = df_trades['pnl_percent'].min()
        
        # Capital metrics
        net_profit = final_capital - initial_capital
        total_return = (net_profit / initial_capital) * 100
        
        # Transaction costs
        total_costs = df_trades['transaction_costs'].sum()
        avg_cost_per_trade = total_costs / total_trades
        
        # Risk metrics
        returns = df_trades['pnl_percent']
        
        # Sharpe Ratio
        if returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # Sortino Ratio (downside deviation only)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = (returns.mean() / downside_returns.std()) * np.sqrt(252)
        else:
            sortino_ratio = 0.0
        
        # Max Drawdown with duration
        cumulative = (1 + returns / 100).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0.0
        
        # Max drawdown duration (simplified - days in drawdown)
        in_drawdown = drawdown < -1  # More than 1% drawdown
        max_dd_duration = 0
        if in_drawdown.any():
            # Count consecutive days in drawdown
            current_duration = 0
            for val in in_drawdown:
                if val:
                    current_duration += 1
                    max_dd_duration = max(max_dd_duration, current_duration)
                else:
                    current_duration = 0
        
        # Profit Factor
        winning_trades = df_trades[df_trades['win'] == True]['net_pnl'].sum()
        losing_trades = abs(df_trades[df_trades['win'] == False]['net_pnl'].sum())
        profit_factor = winning_trades / losing_trades if losing_trades > 0 else 0.0
        
        # Expectancy (average $ per trade)
        expectancy = net_profit / total_trades
        
        # Alpha (excess return vs buy & hold)
        alpha = total_return - buy_hold_return
        
        # Convert trades to TradeRecord models
        trade_records = [
            TradeRecord(
                entry_date=t['entry_date'],
                entry_price=t['entry_price'],
                exit_date=t['exit_date'],
                exit_price=t['exit_price'],
                shares=t['shares'],
                gross_pnl=t['gross_pnl'],
                transaction_costs=t['transaction_costs'],
                net_pnl=t['net_pnl'],
                pnl_percent=t['pnl_percent'],
                win=t['win'],
                exit_reason=t['exit_reason']
            )
            for t in trades[-10:]  # Last 10 trades
        ]
        
        trade_markers = [
            {
                "entry_date": str(t['entry_date']),
                "entry_price": t['entry_price'],
                "exit_date": str(t['exit_date']),
                "exit_price": t['exit_price'],
                "win": t['win']
            }
            for t in trades
        ]
        
        # Calculate actual start date based on requested period
        actual_start_idx = max(0, len(df) - days)
        
        return BacktestResult(
            symbol=symbol,
            strategy_name=strategy.name,
            strategy_config=strategy.config.model_dump(),
            period_days=days,
            start_date=df.index[actual_start_idx],
            end_date=df.index[-1],
            total_trades=total_trades,
            win_rate=round(win_rate, 2),
            avg_return=round(avg_return, 2),
            total_return=round(total_return, 2),
            best_trade=round(best_trade, 2),
            worst_trade=round(worst_trade, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            sortino_ratio=round(sortino_ratio, 2),
            max_drawdown=round(max_drawdown, 2),
            max_drawdown_duration=max_dd_duration,
            profit_factor=round(profit_factor, 2),
            expectancy=round(expectancy, 2),
            total_transaction_costs=round(total_costs, 2),
            avg_cost_per_trade=round(avg_cost_per_trade, 2),
            initial_capital=initial_capital,
            final_capital=round(final_capital, 2),
            net_profit=round(net_profit, 2),
            recent_trades=trade_records,
            price_data=price_data,
            trade_markers=trade_markers,
            buy_and_hold_return=round(buy_hold_return, 2),
            alpha=round(alpha, 2)
        )
    
    async def get_available_strategies(self) -> list[str]:
        """Get list of available strategies"""
        return StrategyFactory.get_available_strategies()
    
    async def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        """Get information about a specific strategy"""
        return StrategyFactory.get_strategy_info(strategy_name)
