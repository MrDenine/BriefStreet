# Strategy Pattern Migration Guide

## 📚 Overview

We've migrated from a hard-coded backtest implementation to a **Strategy Pattern** that allows flexible, extensible trading strategies.

## 🔄 What Changed

### **Before (Old Code):**
```python
# Hard-coded strategy in technical_analysis_service.py
result = await technical_service.backtest(symbol="AAPL", days=365)
# Always used "Buy the Dip" strategy with fixed parameters
```

### **After (New Code):**
```python
# Flexible strategy selection
result = await backtest_service.run_backtest(
    symbol="AAPL",
    strategy_name="buy_the_dip",  # or "mean_reversion", "momentum"
    days=365
)

# Custom configuration
custom_config = StrategyConfig(
    holding_days=7,
    stop_loss_pct=3.0,
    parameters={"rsi_threshold": 30}
)
result = await backtest_service.run_backtest(
    symbol="AAPL",
    strategy_name="buy_the_dip",
    days=365,
    config=custom_config
)
```

## 📁 New File Structure

```
app/
├── strategies/                      # NEW!
│   ├── __init__.py
│   ├── base_strategy.py            # Abstract base class
│   ├── buy_the_dip_strategy.py     # Original strategy (migrated)
│   ├── mean_reversion_strategy.py  # NEW strategy
│   ├── momentum_strategy.py        # NEW strategy
│   └── strategy_factory.py         # Factory pattern
│
├── services/
│   ├── backtest_service.py         # NEW! Dedicated backtest service
│   └── technical_analysis_service.py  # Still exists for live analysis
│
└── api/v1/endpoints/
    └── technical.py                # Updated endpoints
```

## 🎯 Available Strategies

### 1. **Buy The Dip** (Original)
- Entry: Price above EMA + RSI oversold
- Exit: Time-based or stop-loss/take-profit
- Best for: Trending markets with pullbacks

### 2. **Mean Reversion**
- Entry: Price below Bollinger Band + RSI oversold
- Exit: Price returns to mean
- Best for: Range-bound markets

### 3. **Momentum**
- Entry: EMA crossover + RSI strong + ADX trend confirmation
- Exit: Momentum weakens or time-based
- Best for: Strong trending markets

## 🔧 API Endpoints

### **List Available Strategies**
```bash
GET /api/v1/technical/strategies
```

### **Basic Backtest**
```bash
GET /api/v1/technical/backtest/AAPL?strategy=buy_the_dip&days=365
```

### **Custom Configuration**
```bash
POST /api/v1/technical/backtest/AAPL/custom
{
  "strategy_name": "buy_the_dip",
  "config": {
    "name": "buy_the_dip",
    "holding_days": 7,
    "stop_loss_pct": 3.0,
    "take_profit_pct": 15.0,
    "parameters": {
      "ema_length": 150,
      "rsi_threshold": 30
    }
  },
  "days": 365
}
```

## 📊 Enhanced Metrics

The new `BacktestResult` includes:
- **Basic**: total_trades, win_rate, avg_return
- **Advanced**: sharpe_ratio, max_drawdown, profit_factor, total_return
- **Metadata**: strategy_name, strategy_config
- **Trade History**: recent_trades (last 10)

## 🔨 How to Add Your Own Strategy

1. **Create new strategy file:**
```python
# app/strategies/my_strategy.py
from app.strategies.base_strategy import BaseStrategy, StrategyConfig
import pandas as pd

class MyStrategy(BaseStrategy):
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Add your indicators
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # Generate buy signals
        df['Signal'] = your_logic_here
        return df
    
    @classmethod
    def get_default_config(cls) -> StrategyConfig:
        return StrategyConfig(
            name="my_strategy",
            holding_days=5,
            parameters={"param1": value1}
        )
```

2. **Register in factory:**
```python
# app/strategies/strategy_factory.py
from app.strategies.my_strategy import MyStrategy

class StrategyFactory:
    _strategies = {
        "buy_the_dip": BuyTheDipStrategy,
        "mean_reversion": MeanReversionStrategy,
        "momentum": MomentumStrategy,
        "my_strategy": MyStrategy,  # Add here
    }
```

## ⚠️ Breaking Changes

### **API Changes:**
- Old: `GET /api/v1/technical/backtest/{symbol}` 
- New: `GET /api/v1/technical/backtest/{symbol}?strategy=buy_the_dip`

### **Response Model:**
```python
# Old BacktestResult
{
    "symbol": "AAPL",
    "total_trades": 24,
    "win_rate": 62.5,
    # ...
}

# New BacktestResult
{
    "symbol": "AAPL",
    "strategy_name": "buy_the_dip",  # NEW
    "strategy_config": {...},         # NEW
    "total_trades": 24,
    "win_rate": 62.5,
    "sharpe_ratio": 1.45,            # NEW
    "max_drawdown": 8.3,             # NEW
    "profit_factor": 2.1,            # NEW
    # ...
}
```

## 🧪 Testing

Run the example file:
```bash
python examples_strategy_backtest.py
```

## 📈 Next Steps

Future enhancements could include:
- Portfolio backtesting (multiple symbols)
- Walk-forward analysis
- Monte Carlo simulation
- Custom strategy builder UI
- Strategy optimization (parameter tuning)

## ❓ FAQ

**Q: Can I still use the old endpoint?**
A: The endpoint path is the same, but now requires `strategy` parameter. Default is "buy_the_dip" to maintain backward compatibility.

**Q: How do I test multiple strategies at once?**
A: Call the backtest endpoint multiple times with different strategy names, or use the comparison example in `examples_strategy_backtest.py`.

**Q: Can I create strategies without coding?**
A: Not yet, but this architecture makes it possible to build a UI-based strategy builder in the future.
