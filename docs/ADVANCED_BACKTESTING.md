# 🚀 Advanced Backtesting Features Guide

## Overview

This guide covers the new advanced backtesting features designed for **Education** and **Research** use cases with focus on **Performance**, **Accuracy**, and **Scalability**.

---

## 🎯 New Features

### 1. **Transaction Costs** (Realistic Simulation)
- Commission fees (%)
- Slippage (%)
- Minimum commission
- Position sizing based on capital

### 2. **Portfolio Backtesting**
- Test multiple symbols simultaneously
- Portfolio-level metrics
- Correlation analysis
- Capital allocation
- Parallel execution for speed

### 3. **Parameter Optimization**
- Grid search optimization
- Walk-forward analysis
- Overfitting detection
- Multiple optimization metrics
- Out-of-sample testing

---

## 📊 Performance Improvements

### **Speed Optimization:**
- ✅ Parallel backtesting (asyncio)
- ✅ Vectorized calculations (NumPy/Pandas)
- ✅ Efficient data structures
- ✅ Batch processing

### **Accuracy Improvements:**
- ✅ Realistic transaction costs
- ✅ Position sizing constraints
- ✅ Capital tracking
- ✅ Slippage modeling
- ✅ Buy & hold comparison

### **Scalability:**
- ✅ Portfolio of 10+ symbols
- ✅ Parallel optimization (100+ combinations)
- ✅ Multi-year backtests (5+ years)
- ✅ Async API endpoints

---

## 🔧 API Endpoints

### **Basic Backtest**
```bash
GET /api/v1/technical/backtest/{symbol}?strategy=buy_the_dip&days=365
```

### **Custom Configuration**
```bash
POST /api/v1/technical/backtest/{symbol}/custom
{
  "strategy_name": "buy_the_dip",
  "config": {
    "holding_days": 7,
    "stop_loss_pct": 3.0,
    "take_profit_pct": 15.0,
    "parameters": {
      "ema_length": 150,
      "rsi_threshold": 30
    }
  }
}
```

### **Portfolio Backtest**
```bash
POST /api/v1/technical/backtest/portfolio
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "strategy": "buy_the_dip",
  "days": 365,
  "initial_capital": 100000
}
```

### **Strategy Comparison**
```bash
POST /api/v1/technical/backtest/compare-strategies
{
  "symbol": "AAPL",
  "strategies": ["buy_the_dip", "mean_reversion", "momentum"],
  "days": 365
}
```

### **Parameter Optimization**
```bash
POST /api/v1/technical/optimize/AAPL?strategy=buy_the_dip&metric=sharpe_ratio
```

### **Walk-Forward Analysis**
```bash
POST /api/v1/technical/optimize/AAPL/walk-forward?strategy=buy_the_dip&total_days=730
```

---

## 💻 Code Examples

### **1. Realistic Backtest**
```python
from app.models.backtest import TransactionCosts, PositionSizing

# Configure costs
transaction_costs = TransactionCosts(
    commission_pct=0.1,   # 0.1% commission
    slippage_pct=0.05,    # 0.05% slippage
    min_commission=1.0    # $1 minimum
)

position_sizing = PositionSizing(
    initial_capital=100000.0,
    max_position_pct=20.0,  # Max 20% per trade
    max_positions=5
)

service = BacktestService(data_provider, transaction_costs, position_sizing)

result = await service.run_backtest(
    symbol="AAPL",
    strategy_name="buy_the_dip",
    days=365,
    initial_capital=100000.0
)

print(f"Net Profit: ${result.net_profit:,.2f}")
print(f"Alpha: {result.alpha:.2f}%")
print(f"Transaction Costs: ${result.total_transaction_costs:.2f}")
```

### **2. Portfolio Backtest**
```python
service = PortfolioBacktestService(data_provider)

result = await service.run_portfolio_backtest(
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN"],
    strategy_name="buy_the_dip",
    days=365,
    initial_capital=100000.0
)

print(f"Portfolio Return: {result.total_return:.2f}%")
print(f"Best Performer: {result.best_performer}")
print(f"Diversification (Avg Correlation): {result.avg_correlation:.2f}")
```

### **3. Parameter Optimization**
```python
from app.services.optimization_service import ParameterRange

# Define what to optimize
param_ranges = [
    ParameterRange("ema_length", [150, 200, 250], True),
    ParameterRange("rsi_threshold", [30, 35, 40], True),
    ParameterRange("holding_days", [5, 7, 10], False),
]

service = ParameterOptimizationService(data_provider)

result = await service.optimize_grid_search(
    symbol="AAPL",
    strategy_name="buy_the_dip",
    parameter_ranges=param_ranges,
    optimization_metric="sharpe_ratio"
)

print(f"Best Sharpe: {result.best_score:.2f}")
print(f"Best Params: {result.best_config.parameters}")
```

### **4. Walk-Forward Analysis**
```python
result = await service.walk_forward_analysis(
    symbol="AAPL",
    strategy_name="buy_the_dip",
    parameter_ranges=param_ranges,
    total_days=730  # 2 years: 60% train, 20% val, 20% test
)

print(f"Train Sharpe: {result['train']['metric']:.2f}")
print(f"Test Sharpe: {result['test']['metric']:.2f}")
print(f"Overfitting: {result['overfitting_score']:.1f}%")

if result['overfitting_score'] < 10:
    print("✅ Strategy is robust!")
```

---

## 📈 Enhanced Metrics

### **Capital Metrics:**
- `initial_capital`: Starting capital
- `final_capital`: Ending capital
- `net_profit`: Profit in dollars
- `total_return`: Return percentage

### **Performance Metrics:**
- `win_rate`: % of winning trades
- `avg_return`: Average return per trade
- `total_return`: Cumulative return
- `expectancy`: Expected value per trade

### **Risk Metrics:**
- `sharpe_ratio`: Risk-adjusted return
- `sortino_ratio`: Downside risk-adjusted return
- `max_drawdown`: Maximum peak-to-trough decline
- `max_drawdown_duration`: Days in drawdown
- `profit_factor`: Gross profit / Gross loss

### **Cost Metrics:**
- `total_transaction_costs`: Total fees paid
- `avg_cost_per_trade`: Average cost per trade

### **Comparison Metrics:**
- `buy_and_hold_return`: Benchmark return
- `alpha`: Excess return vs benchmark

---

## 🎓 Educational Use Cases

### **1. Learning Trading Strategies**
```python
# Compare 3 strategies to understand differences
results = await service.compare_strategies(
    symbol="AAPL",
    strategy_names=["buy_the_dip", "mean_reversion", "momentum"]
)

# See which works best and why
for name, result in results.items():
    print(f"{name}: {result.total_return:.2f}%")
```

### **2. Understanding Risk**
```python
# Run backtest and examine risk metrics
result = await service.run_backtest(symbol="TSLA", days=365)

print(f"Return: {result.total_return:.2f}%")
print(f"Risk (Max DD): {result.max_drawdown:.2f}%")
print(f"Risk-Adjusted (Sharpe): {result.sharpe_ratio:.2f}")

# High return but high risk? Or consistent performance?
```

### **3. Impact of Transaction Costs**
```python
# Test with different cost structures
costs_low = TransactionCosts(commission_pct=0.05, slippage_pct=0.02)
costs_high = TransactionCosts(commission_pct=0.5, slippage_pct=0.2)

result_low = await BacktestService(data, costs_low).run_backtest(...)
result_high = await BacktestService(data, costs_high).run_backtest(...)

print(f"With low costs: {result_low.total_return:.2f}%")
print(f"With high costs: {result_high.total_return:.2f}%")
print(f"Impact: {result_low.total_return - result_high.total_return:.2f}%")
```

---

## 🔬 Research Use Cases

### **1. Strategy Development**
```python
# Optimize parameters
opt_result = await service.optimize_grid_search(
    symbol="AAPL",
    strategy_name="buy_the_dip",
    parameter_ranges=[...],
    optimization_metric="sharpe_ratio"
)

# Use best parameters for production
best_config = opt_result.best_config
```

### **2. Backtesting Ideas**
```python
# Test custom strategy idea
custom_config = StrategyConfig(
    name="my_idea",
    holding_days=3,  # Quick exits
    stop_loss_pct=2.0,  # Tight stop
    parameters={"rsi_threshold": 25}  # Very oversold
)

result = await service.run_backtest(
    symbol="AAPL",
    strategy_name="buy_the_dip",
    config=custom_config
)

# Did it work? Check the metrics!
```

### **3. Overfitting Detection**
```python
# Ensure strategy isn't curve-fitted
wf_result = await service.walk_forward_analysis(
    symbol="AAPL",
    strategy_name="my_strategy",
    total_days=1095  # 3 years
)

if wf_result['overfitting_score'] > 30:
    print("⚠️ Warning: Strategy may be overfit!")
else:
    print("✅ Strategy appears robust")
```

---

## ⚡ Performance Tips

### **For Speed:**
1. Use portfolio backtesting for multiple symbols (parallel)
2. Limit optimization combinations (use sensible ranges)
3. Cache historical data when testing multiple strategies
4. Use `max_parallel` parameter in optimization

### **For Accuracy:**
1. Always include transaction costs
2. Use walk-forward analysis for validation
3. Compare to buy & hold benchmark
4. Test across multiple market conditions

### **For Scalability:**
1. Use async/await for concurrent operations
2. Batch operations when possible
3. Limit data fetch size (use appropriate `days` parameter)
4. Monitor memory usage with large portfolios

---

## 📚 Next Steps

1. **Try Examples**: Run `python examples_advanced_backtest.py`
2. **Test API**: Start server and use Swagger docs at `/docs`
3. **Optimize**: Find best parameters for your favorite strategy
4. **Research**: Test new strategy ideas with walk-forward analysis
5. **Learn**: Compare strategies to understand what works

---

## ❓ FAQ

**Q: Why are my returns different from before?**
A: Transaction costs are now included. This is more realistic!

**Q: How do I know if I'm overfitting?**
A: Use walk-forward analysis. If overfitting score > 30%, be careful.

**Q: Can I backtest my own strategy?**
A: Yes! Create a new strategy class following the pattern in `app/strategies/`

**Q: How many symbols can I backtest at once?**
A: Tested with 10+ symbols. Performance depends on your system.

**Q: Which optimization metric should I use?**
A: For education: Sharpe ratio (risk-adjusted). For max returns: total_return.

---

## 🎯 Best Practices

1. ✅ Always use realistic transaction costs
2. ✅ Test across multiple timeframes (1Y, 2Y, 3Y)
3. ✅ Use walk-forward for validation
4. ✅ Compare to buy & hold benchmark
5. ✅ Check correlation when building portfolios
6. ✅ Don't over-optimize (keep it simple)
7. ✅ Test in different market conditions
8. ✅ Document your assumptions

---

**Happy Backtesting! 🚀📈**
