"""
Advanced Backtesting Examples

Demonstrates the new features:
1. Transaction Costs (Realistic Simulation)
2. Portfolio Backtesting
3. Parameter Optimization
"""

import asyncio
from app.data_sources.yfinance_provider import YFinanceProvider
from app.services.backtest_service import BacktestService
from app.services.portfolio_backtest_service import PortfolioBacktestService
from app.services.optimization_service import ParameterOptimizationService, ParameterRange
from app.models.backtest import TransactionCosts, PositionSizing
from app.strategies.base_strategy import StrategyConfig


# ============================================================================
# Example 1: Realistic Backtest with Transaction Costs
# ============================================================================

async def example_realistic_backtest():
    """
    Backtest with realistic transaction costs and position sizing.
    """
    print("\n" + "="*80)
    print("Example 1: Realistic Backtest with Transaction Costs")
    print("="*80)
    
    # Configure realistic costs
    transaction_costs = TransactionCosts(
        commission_pct=0.1,      # 0.1% commission
        slippage_pct=0.05,       # 0.05% slippage
        min_commission=1.0       # $1 minimum
    )
    
    position_sizing = PositionSizing(
        initial_capital=100000.0,
        max_position_pct=20.0,   # Max 20% per position
        max_positions=5
    )
    
    # Create service
    data_provider = YFinanceProvider()
    service = BacktestService(data_provider, transaction_costs, position_sizing)
    
    # Run backtest
    result = await service.run_backtest(
        symbol="AAPL",
        strategy_name="buy_the_dip",
        days=365,
        initial_capital=100000.0
    )
    
    # Display results
    print(f"\n📊 Results for {result.symbol} ({result.strategy_name})")
    print(f"   Period: {result.start_date.date()} to {result.end_date.date()}")
    print(f"\n💰 Capital:")
    print(f"   Initial: ${result.initial_capital:,.2f}")
    print(f"   Final: ${result.final_capital:,.2f}")
    print(f"   Net Profit: ${result.net_profit:,.2f} ({result.total_return:.2f}%)")
    print(f"\n📈 Performance:")
    print(f"   Total Trades: {result.total_trades}")
    print(f"   Win Rate: {result.win_rate}%")
    print(f"   Avg Return: {result.avg_return}%")
    print(f"   Best Trade: {result.best_trade}%")
    print(f"   Worst Trade: {result.worst_trade}%")
    print(f"\n⚖️  Risk Metrics:")
    print(f"   Sharpe Ratio: {result.sharpe_ratio}")
    print(f"   Sortino Ratio: {result.sortino_ratio}")
    print(f"   Max Drawdown: {result.max_drawdown}%")
    print(f"   Profit Factor: {result.profit_factor}")
    print(f"\n💸 Transaction Costs:")
    print(f"   Total Costs: ${result.total_transaction_costs:,.2f}")
    print(f"   Avg per Trade: ${result.avg_cost_per_trade:.2f}")
    print(f"\n🎯 Benchmark:")
    print(f"   Buy & Hold: {result.buy_and_hold_return}%")
    print(f"   Alpha: {result.alpha}%")


# ============================================================================
# Example 2: Portfolio Backtesting
# ============================================================================

async def example_portfolio_backtest():
    """
    Backtest a portfolio of multiple symbols.
    """
    print("\n" + "="*80)
    print("Example 2: Portfolio Backtesting (Tech Giants)")
    print("="*80)
    
    data_provider = YFinanceProvider()
    service = PortfolioBacktestService(data_provider)
    
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]
    
    result = await service.run_portfolio_backtest(
        symbols=symbols,
        strategy_name="buy_the_dip",
        days=365,
        initial_capital=100000.0
    )
    
    print(f"\n📊 Portfolio Results:")
    print(f"   Symbols: {', '.join(result.symbols)}")
    print(f"   Strategy: {result.strategy_name}")
    print(f"\n💰 Portfolio Metrics:")
    print(f"   Initial Capital: ${result.initial_capital:,.2f}")
    print(f"   Final Capital: ${result.final_capital:,.2f}")
    print(f"   Net Profit: ${result.net_profit:,.2f}")
    print(f"   Total Return: {result.total_return}%")
    print(f"\n📈 Performance:")
    print(f"   Sharpe Ratio: {result.sharpe_ratio}")
    print(f"   Max Drawdown: {result.max_drawdown}%")
    print(f"   Avg Correlation: {result.avg_correlation:.2f}")
    print(f"\n🏆 Top Performer: {result.best_performer}")
    print(f"😞 Worst Performer: {result.worst_performer}")
    
    print(f"\n📋 Individual Results:")
    for symbol, res in result.individual_results.items():
        print(f"   {symbol:6s}: {res.total_return:>7.2f}% | "
              f"Win Rate: {res.win_rate:>5.1f}% | "
              f"Trades: {res.total_trades:>3d}")


# ============================================================================
# Example 3: Strategy Comparison
# ============================================================================

async def example_strategy_comparison():
    """
    Compare multiple strategies on the same symbol.
    """
    print("\n" + "="*80)
    print("Example 3: Strategy Comparison (TSLA)")
    print("="*80)
    
    data_provider = YFinanceProvider()
    service = PortfolioBacktestService(data_provider)
    
    strategies = ["buy_the_dip", "mean_reversion", "momentum"]
    
    results = await service.compare_strategies(
        symbol="TSLA",
        strategy_names=strategies,
        days=365
    )
    
    print(f"\n📊 Strategy Comparison Results:\n")
    print(f"{'Strategy':<20} {'Return %':<12} {'Sharpe':<10} {'Win Rate':<10} {'Trades':<10}")
    print("-" * 70)
    
    for strategy_name, result in sorted(
        results.items(), 
        key=lambda x: x[1].total_return, 
        reverse=True
    ):
        print(f"{strategy_name:<20} {result.total_return:>10.2f}% "
              f"{result.sharpe_ratio:>9.2f} "
              f"{result.win_rate:>9.1f}% "
              f"{result.total_trades:>9d}")


# ============================================================================
# Example 4: Parameter Optimization
# ============================================================================

async def example_parameter_optimization():
    """
    Find optimal parameters using grid search.
    """
    print("\n" + "="*80)
    print("Example 4: Parameter Optimization (Buy The Dip on AAPL)")
    print("="*80)
    
    data_provider = YFinanceProvider()
    service = ParameterOptimizationService(data_provider)
    
    # Define parameter ranges
    param_ranges = [
        ParameterRange("ema_length", [150, 200, 250], True),
        ParameterRange("rsi_threshold", [30, 35, 40], True),
        ParameterRange("holding_days", [5, 7, 10], False),
    ]
    
    result = await service.optimize_grid_search(
        symbol="AAPL",
        strategy_name="buy_the_dip",
        parameter_ranges=param_ranges,
        days=365,
        optimization_metric="sharpe_ratio",
        max_parallel=3
    )
    
    print(f"\n✅ Optimization Complete!")
    print(f"   Total Combinations: {result.total_combinations}")
    print(f"   Time Taken: {result.optimization_time:.1f}s")
    print(f"\n🏆 Best Configuration:")
    print(f"   Metric ({result.optimization_metric}): {result.best_score:.2f}")
    print(f"   Parameters: {result.best_config['parameters']}")
    print(f"   Holding Days: {result.best_config['holding_days']}")
    print(f"   Stop Loss: {result.best_config['stop_loss_pct']}%")
    print(f"   Take Profit: {result.best_config['take_profit_pct']}%")
    
    print(f"\n📊 Top 5 Configurations:")
    for i, config in enumerate(result.top_results[:5], 1):
        print(f"   #{i}: Score={config['metric_value']:.2f} | "
              f"Return={config['total_return']:.2f}% | "
              f"Params={config['parameters']}")


# ============================================================================
# Example 5: Walk-Forward Analysis
# ============================================================================

async def example_walk_forward():
    """
    Perform walk-forward analysis to test for overfitting.
    """
    print("\n" + "="*80)
    print("Example 5: Walk-Forward Analysis (Overfitting Detection)")
    print("="*80)
    
    data_provider = YFinanceProvider()
    service = ParameterOptimizationService(data_provider)
    
    param_ranges = service.get_default_ranges("buy_the_dip")
    
    result = await service.walk_forward_analysis(
        symbol="AAPL",
        strategy_name="buy_the_dip",
        parameter_ranges=param_ranges,
        total_days=730,  # 2 years
        optimization_metric="sharpe_ratio"
    )
    
    print(f"\n📊 Walk-Forward Results:")
    print(f"   Train: {result['train']['metric']:.2f}")
    print(f"   Validation: {result['validation']['metric']:.2f}")
    print(f"   Test (Out-of-Sample): {result['test']['metric']:.2f}")
    print(f"\n⚠️  Overfitting Score: {result['overfitting_score']:.1f}%")
    
    if result['overfitting_score'] > 30:
        print(f"   ❌ High overfitting risk - strategy may not generalize well")
    elif result['overfitting_score'] < 10:
        print(f"   ✅ Low overfitting - strategy appears robust")
    else:
        print(f"   ⚠️  Moderate overfitting - use with caution")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run all examples"""
    print("\n🚀 Advanced Backtesting Examples")
    print("="*80)
    
    # Run examples (comment out ones you don't want to run)
    await example_realistic_backtest()
    await example_portfolio_backtest()
    await example_strategy_comparison()
    await example_parameter_optimization()
    await example_walk_forward()
    
    print("\n" + "="*80)
    print("✅ Examples completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
