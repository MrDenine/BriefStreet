"""
Backtest Models

Enhanced models for realistic backtesting with transaction costs and portfolio support.
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.strategies.base_strategy import StrategyConfig


# ============================================================================
# Transaction Cost Configuration
# ============================================================================

class TransactionCosts(BaseModel):
    """
    Configuration for realistic transaction costs.
    
    Attributes:
        commission_pct: Commission as percentage of trade value (default: 0.1%)
        slippage_pct: Slippage as percentage of trade value (default: 0.05%)
        min_commission: Minimum commission per trade (default: 0.0)
    """
    commission_pct: float = Field(0.1, ge=0, le=10, description="Commission percentage")
    slippage_pct: float = Field(0.05, ge=0, le=5, description="Slippage percentage")
    min_commission: float = Field(0.0, ge=0, description="Minimum commission per trade")
    
    def calculate_costs(self, trade_value: float) -> float:
        """
        Calculate total transaction costs for a trade.
        
        Args:
            trade_value: Total value of the trade
            
        Returns:
            Total cost including commission and slippage
        """
        commission = max(
            trade_value * (self.commission_pct / 100),
            self.min_commission
        )
        slippage = trade_value * (self.slippage_pct / 100)
        return commission + slippage
    
    class Config:
        json_schema_extra = {
            "example": {
                "commission_pct": 0.1,
                "slippage_pct": 0.05,
                "min_commission": 1.0
            }
        }


# ============================================================================
# Position Sizing Configuration
# ============================================================================

class PositionSizing(BaseModel):
    """
    Configuration for position sizing rules.
    
    Attributes:
        initial_capital: Starting capital (default: 100,000)
        max_position_pct: Maximum % of capital per position (default: 20%)
        max_positions: Maximum concurrent positions (default: unlimited)
        sizing_method: Method for calculating position size
    """
    initial_capital: float = Field(100000.0, gt=0, description="Initial capital")
    max_position_pct: float = Field(20.0, ge=1, le=100, description="Max % per position")
    max_positions: int = Field(0, ge=0, description="Max concurrent positions (0=unlimited)")
    sizing_method: str = Field("fixed_pct", description="Sizing method: fixed_pct, fixed_amount, kelly")
    
    def calculate_position_size(
        self, 
        current_capital: float, 
        price: float
    ) -> int:
        """
        Calculate number of shares to buy.
        
        Args:
            current_capital: Current portfolio capital
            price: Current price per share
            
        Returns:
            Number of shares to buy
        """
        max_value = current_capital * (self.max_position_pct / 100)
        shares = int(max_value / price)
        return shares
    
    class Config:
        json_schema_extra = {
            "example": {
                "initial_capital": 100000.0,
                "max_position_pct": 20.0,
                "max_positions": 5,
                "sizing_method": "fixed_pct"
            }
        }


# ============================================================================
# Enhanced Trade Record
# ============================================================================

class TradeRecord(BaseModel):
    """
    Detailed record of a single trade with costs.
    """
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    shares: int = Field(1, description="Number of shares traded")
    gross_pnl: float = Field(..., description="P&L before costs")
    transaction_costs: float = Field(0.0, description="Total transaction costs")
    net_pnl: float = Field(..., description="P&L after costs")
    pnl_percent: float = Field(..., description="Return percentage (net)")
    win: bool = Field(..., description="Whether trade was profitable")
    exit_reason: str = Field("TIME_BASED", description="Reason for exit")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entry_date": "2025-01-15T00:00:00",
                "entry_price": 150.0,
                "exit_date": "2025-01-20T00:00:00",
                "exit_price": 157.5,
                "shares": 100,
                "gross_pnl": 750.0,
                "transaction_costs": 30.75,
                "net_pnl": 719.25,
                "pnl_percent": 4.79,
                "win": True,
                "exit_reason": "TAKE_PROFIT"
            }
        }


# ============================================================================
# Enhanced Backtest Result
# ============================================================================

class BacktestResult(BaseModel):
    """
    Comprehensive backtest results with realistic metrics.
    """
    symbol: str
    strategy_name: str = Field(default="buy_the_dip", description="Strategy used")
    strategy_config: dict = Field(default_factory=dict, description="Strategy configuration")
    
    # Period & Basic Stats
    period_days: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_trades: int
    
    # Performance Metrics
    win_rate: float = Field(..., description="Percentage of winning trades")
    avg_return: float = Field(..., description="Average return per trade (%)")
    total_return: float = Field(0.0, description="Total cumulative return (%)")
    best_trade: float = Field(..., description="Best trade return (%)")
    worst_trade: float = Field(..., description="Worst trade return (%)")
    
    # Risk Metrics
    sharpe_ratio: float = Field(0.0, description="Risk-adjusted return")
    sortino_ratio: float = Field(0.0, description="Downside risk-adjusted return")
    max_drawdown: float = Field(0.0, description="Maximum drawdown (%)")
    max_drawdown_duration: int = Field(0, description="Max drawdown duration (days)")
    
    # Profitability Metrics
    profit_factor: float = Field(0.0, description="Gross profit / Gross loss")
    expectancy: float = Field(0.0, description="Expected value per trade")
    
    # Transaction Costs
    total_transaction_costs: float = Field(0.0, description="Total costs incurred")
    avg_cost_per_trade: float = Field(0.0, description="Average cost per trade")
    
    # Capital Metrics
    initial_capital: float = Field(100000.0, description="Starting capital")
    final_capital: float = Field(100000.0, description="Ending capital")
    net_profit: float = Field(0.0, description="Net profit (final - initial)")
    
    # Trade Details
    recent_trades: List[TradeRecord] = Field(default_factory=list, description="Recent trades")
    
    # Chart Data
    price_data: Optional[List[Dict[str, Any]]] = Field(None, description="OHLC price data for plotting")
    trade_markers: Optional[List[Dict[str, Any]]] = Field(None, description="Trade entry/exit markers for plotting")
    
    # Comparison
    buy_and_hold_return: float = Field(0.0, description="Buy & hold return (%)")
    alpha: float = Field(0.0, description="Excess return vs buy & hold")
    
    def plot_backtest(self, figsize=(14, 8)):
        """
        Plot backtest results with price chart and trade markers.
        
        Args:
            figsize: Figure size (width, height)
            
        Returns:
            matplotlib figure object
            
        Example:
            result = await backtest_service.run_backtest(...)
            fig = result.plot_backtest()
            plt.show()
        """
        try:
            import matplotlib.pyplot as plt
            import pandas as pd
        except ImportError:
            raise ImportError("matplotlib and pandas required for plotting. Install with: pip install matplotlib pandas")
        
        if not self.price_data or not self.trade_markers:
            raise ValueError("No chart data available. Make sure price_data and trade_markers are populated.")
        
        # Prepare data
        df_price = pd.DataFrame(self.price_data)
        df_price['timestamp'] = pd.to_datetime(df_price['timestamp'])
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot price
        ax.plot(df_price['timestamp'], df_price['close'], 
                label='Close Price', color='#2E86AB', linewidth=1.5, alpha=0.8)
        
        # Plot trade markers
        for trade in self.trade_markers:
            entry_date = pd.to_datetime(trade['entry_date'])
            exit_date = pd.to_datetime(trade['exit_date'])
            
            # Entry marker (green triangle up)
            ax.scatter(entry_date, trade['entry_price'], 
                      color='#06D6A0', marker='^', s=150, 
                      edgecolors='black', linewidths=1, zorder=5, alpha=0.9)
            
            # Exit marker (color based on win/loss)
            exit_color = '#06D6A0' if trade['win'] else '#EF476F'
            ax.scatter(exit_date, trade['exit_price'], 
                      color=exit_color, marker='v', s=150, 
                      edgecolors='black', linewidths=1, zorder=5, alpha=0.9)
            
            # Connect entry and exit with line
            line_color = '#A8DADC' if trade['win'] else '#F78C6B'
            ax.plot([entry_date, exit_date], 
                   [trade['entry_price'], trade['exit_price']], 
                   color=line_color, linestyle='--', linewidth=1, alpha=0.5)
        
        # Formatting
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel('Price', fontsize=11, fontweight='bold')
        ax.set_title(f'{self.symbol} - {self.strategy_name} Backtest Results', 
                    fontsize=14, fontweight='bold', pad=15)
        
        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#2E86AB', label='Price'),
            plt.scatter([], [], color='#06D6A0', marker='^', s=100, 
                       edgecolors='black', linewidths=1, label='Entry'),
            plt.scatter([], [], color='#06D6A0', marker='v', s=100, 
                       edgecolors='black', linewidths=1, label='Exit (Win)'),
            plt.scatter([], [], color='#EF476F', marker='v', s=100, 
                       edgecolors='black', linewidths=1, label='Exit (Loss)')
        ]
        ax.legend(handles=legend_elements, loc='best', fontsize=10)
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add performance metrics as text box
        metrics_text = (
            f"Total Return: {self.total_return:.2f}%\n"
            f"Win Rate: {self.win_rate:.1f}%\n"
            f"Sharpe Ratio: {self.sharpe_ratio:.2f}\n"
            f"Total Trades: {self.total_trades}\n"
            f"Alpha vs B&H: {self.alpha:+.2f}%"
        )
        ax.text(0.02, 0.98, metrics_text, 
               transform=ax.transAxes, fontsize=9,
               verticalalignment='top', 
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        return fig

    def plot_price_data(self, figsize=(14, 8)):
        """
        Plot detailed price data with volume.
        
        Args:
            figsize: Figure size (width, height)
            
        Returns:
            matplotlib figure object
        """
        try:
            import matplotlib.pyplot as plt
            import pandas as pd
        except ImportError:
            raise ImportError("matplotlib and pandas required for plotting.")
        
        if not self.price_data:
            raise ValueError("No price data available.")
        
        # Prepare data
        df_price = pd.DataFrame(self.price_data)
        df_price['timestamp'] = pd.to_datetime(df_price['timestamp'])
        
        # Create figure with 2 subplots (Price and Volume)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, 
                                      gridspec_kw={'height_ratios': [3, 1]}, 
                                      sharex=True)
        
        # Plot Price
        ax1.plot(df_price['timestamp'], df_price['close'], 
                label='Close', color='#2E86AB', linewidth=1.5)
        
        # Add High-Low range if available
        if 'high' in df_price.columns and 'low' in df_price.columns:
            ax1.fill_between(df_price['timestamp'], 
                           df_price['low'], 
                           df_price['high'], 
                           color='#2E86AB', alpha=0.1, label='High-Low Range')
            
        ax1.set_title(f'{self.symbol} Price Analysis', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')
        
        # Plot Volume
        if 'volume' in df_price.columns:
            # Color volume bars based on price change
            colors = ['#2E86AB'] * len(df_price)
            if 'open' in df_price.columns:
                colors = ['#06D6A0' if c >= o else '#EF476F' 
                         for c, o in zip(df_price['close'], df_price['open'])]
            
            ax2.bar(df_price['timestamp'], df_price['volume'], color=colors, alpha=0.8)
            
        ax2.set_ylabel('Volume', fontsize=11)
        ax2.set_xlabel('Date', fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "strategy_name": "buy_the_dip",
                "period_days": 365,
                "total_trades": 24,
                "win_rate": 62.5,
                "avg_return": 2.34,
                "total_return": 56.16,
                "sharpe_ratio": 1.45,
                "max_drawdown": 8.3,
                "profit_factor": 2.1,
                "initial_capital": 100000.0,
                "final_capital": 115616.0,
                "net_profit": 15616.0,
                "buy_and_hold_return": 28.5,
                "alpha": 27.66
            }
        }


# ============================================================================
# Portfolio Backtest Models
# ============================================================================

class PortfolioPosition(BaseModel):
    """Current position in portfolio"""
    symbol: str
    shares: int
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    weight: float = Field(..., description="Position weight in portfolio (%)")


class PortfolioBacktestResult(BaseModel):
    """
    Results from portfolio backtesting (multiple symbols).
    """
    symbols: List[str]
    strategy_name: str
    period_days: int
    
    # Portfolio Metrics
    total_return: float = Field(..., description="Portfolio total return (%)")
    sharpe_ratio: float = Field(0.0, description="Portfolio Sharpe ratio")
    max_drawdown: float = Field(0.0, description="Portfolio max drawdown (%)")
    
    # Individual Results
    individual_results: Dict[str, BacktestResult] = Field(
        default_factory=dict,
        description="Results for each symbol"
    )
    
    # Capital Allocation
    initial_capital: float
    final_capital: float
    net_profit: float
    
    # Correlation
    avg_correlation: float = Field(0.0, description="Average correlation between assets")
    
    # Comparison
    best_performer: str = Field("", description="Best performing symbol")
    worst_performer: str = Field("", description="Worst performing symbol")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["AAPL", "MSFT", "GOOGL"],
                "strategy_name": "buy_the_dip",
                "period_days": 365,
                "total_return": 45.2,
                "sharpe_ratio": 1.8,
                "max_drawdown": 12.5,
                "initial_capital": 100000.0,
                "final_capital": 145200.0,
                "net_profit": 45200.0,
                "best_performer": "MSFT",
                "worst_performer": "GOOGL"
            }
        }


# ============================================================================
# Optimization Models
# ============================================================================

class OptimizationResult(BaseModel):
    """
    Results from parameter optimization.
    """
    strategy_name: str
    symbol: str
    optimization_metric: str = Field("sharpe_ratio", description="Metric being optimized")
    
    # Best Configuration
    best_config: Dict[str, Any] = Field(..., description="Best parameter configuration")
    best_score: float = Field(..., description="Best metric value achieved")
    
    # All Results
    total_combinations: int = Field(..., description="Total combinations tested")
    top_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top 10 configurations"
    )
    
    # Performance
    optimization_time: float = Field(..., description="Time taken (seconds)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_name": "buy_the_dip",
                "symbol": "AAPL",
                "optimization_metric": "sharpe_ratio",
                "best_score": 1.95,
                "total_combinations": 120,
                "optimization_time": 45.2
            }
        }



