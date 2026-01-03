"""
Example: How to use the new Strategy Pattern for Backtesting

This file demonstrates how to use different strategies with the backtest system.
"""

import asyncio
from app.data_sources.yfinance_provider import YFinanceProvider
from app.services.backtest_service import BacktestService
from app.strategies.base_strategy import StrategyConfig
from app.strategies.strategy_factory import StrategyFactory


async def example_basic_backtest():
    """Example 1: Run backtest with default strategy"""
    print("\n" + "="*60)
    print("Example 1: Basic Backtest with Default Strategy")
    print("="*60)
    
    # Create service
    data_provider = YFinanceProvider()
    backtest_service = BacktestService(data_provider)
    
    # Run backtest with default "buy_the_dip" strategy
    result = await backtest_service.run_backtest(
        symbol="AAPL",
        strategy_name="buy_the_dip",
        days=365
    )
    
    print(f"\n📊 Results for {result.symbol}:")
    print(f"   Strategy: {result.strategy_name}")
    print(f"   Total Trades: {result.total_trades}")
    print(f"   Win Rate: {result.win_rate}%")
    print(f"   Avg Return: {result.avg_return}%")
    print(f"   Total Return: {result.total_return}%")
    print(f"   Sharpe Ratio: {result.sharpe_ratio}")
    print(f"   Max Drawdown: {result.max_drawdown}%")
    print(f"   Profit Factor: {result.profit_factor}")


async def example_different_strategies():
    """Example 2: Compare different strategies"""
    print("\n" + "="*60)
    print("Example 2: Compare Multiple Strategies")
    print("="*60)
    
    data_provider = YFinanceProvider()
    backtest_service = BacktestService(data_provider)
    
    strategies = ["buy_the_dip", "mean_reversion", "momentum"]
    symbol = "TSLA"
    days = 365
    
    for strategy_name in strategies:
        try:
            result = await backtest_service.run_backtest(
                symbol=symbol,
                strategy_name=strategy_name,
                days=days
            )
            
            print(f"\n📈 {strategy_name.upper()}:")
            print(f"   Trades: {result.total_trades} | Win Rate: {result.win_rate}% | Avg: {result.avg_return}%")
            print(f"   Sharpe: {result.sharpe_ratio} | Max DD: {result.max_drawdown}%")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")


async def example_custom_config():
    """Example 3: Use custom strategy configuration"""
    print("\n" + "="*60)
    print("Example 3: Custom Strategy Configuration")
    print("="*60)
    
    data_provider = YFinanceProvider()
    backtest_service = BacktestService(data_provider)
    
    # Create custom config with tighter stop loss
    custom_config = StrategyConfig(
        name="buy_the_dip",
        holding_days=7,          # Hold longer
        stop_loss_pct=3.0,       # Tighter stop loss
        take_profit_pct=15.0,    # Higher take profit
        parameters={
            "ema_length": 150,   # Shorter EMA
            "rsi_threshold": 30  # More oversold
        }
    )
    
    result = await backtest_service.run_backtest(
        symbol="BTC-USD",
        strategy_name="buy_the_dip",
        days=365,
        config=custom_config
    )
    
    print(f"\n📊 Custom Config Results:")
    print(f"   Config: {result.strategy_config}")
    print(f"   Win Rate: {result.win_rate}%")
    print(f"   Total Return: {result.total_return}%")


async def example_list_strategies():
    """Example 4: List all available strategies"""
    print("\n" + "="*60)
    print("Example 4: Available Strategies")
    print("="*60)
    
    strategies = StrategyFactory.get_available_strategies()
    
    print(f"\n📚 Available Strategies: {len(strategies)}")
    for name in strategies:
        info = StrategyFactory.get_strategy_info(name)
        print(f"\n   • {name.upper()}")
        print(f"     - Holding Days: {info['holding_days']}")
        print(f"     - Stop Loss: {info['stop_loss_pct']}%")
        print(f"     - Take Profit: {info['take_profit_pct']}%")
        print(f"     - Parameters: {info['parameters']}")


async def main():
    """Run all examples"""
    print("\n🚀 Strategy Pattern Backtest Examples")
    print("="*60)
    
    # Run examples
    # await example_basic_backtest()
    # await example_different_strategies()
    # await example_custom_config()
    await example_list_strategies()
    
    print("\n" + "="*60)
    print("✅ Examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
