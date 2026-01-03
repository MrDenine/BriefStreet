"""
Parameter Optimization Service

Service for finding optimal strategy parameters using grid search and walk-forward analysis.
"""

import asyncio
import time
from itertools import product
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from app.data_sources.base import DataSourceProvider
from app.strategies.base_strategy import StrategyConfig
from app.strategies.strategy_factory import StrategyFactory
from app.services.backtest_service import BacktestService
from app.models.backtest import OptimizationResult, BacktestResult, TransactionCosts, PositionSizing


@dataclass
class ParameterRange:
    """Define a range for a parameter to optimize"""
    name: str
    values: List[Any]
    is_strategy_param: bool = True  # True if in strategy.parameters, False if in strategy config


class ParameterOptimizationService:
    """
    Service for optimizing strategy parameters.
    
    Features:
    - Grid search optimization
    - Multiple optimization metrics
    - Walk-forward analysis
    - Out-of-sample testing
    - Parallel execution for speed
    """
    
    def __init__(
        self,
        backtest_service: BacktestService
    ):
        """
        Initialize optimization service.
        
        Args:
            backtest_service: BacktestService instance to use for optimization
        """
        self.backtest_service = backtest_service
    
    async def optimize_grid_search(
        self,
        symbol: str,
        strategy_name: str,
        parameter_ranges: List[ParameterRange],
        days: int = 365,
        optimization_metric: str = "sharpe_ratio",
        max_parallel: int = 5
    ) -> OptimizationResult:
        """
        Find optimal parameters using grid search.
        
        Args:
            symbol: Ticker symbol
            strategy_name: Strategy to optimize
            parameter_ranges: List of parameter ranges to test
            days: Backtest period
            optimization_metric: Metric to optimize (sharpe_ratio, total_return, profit_factor, etc.)
            max_parallel: Maximum parallel backtests
            
        Returns:
            OptimizationResult with best configuration
        """
        start_time = time.time()
        
        # Generate all parameter combinations
        param_names = [p.name for p in parameter_ranges]
        param_values = [p.values for p in parameter_ranges]
        param_is_strategy = [p.is_strategy_param for p in parameter_ranges]
        
        combinations = list(product(*param_values))
        total_combinations = len(combinations)
        
        print(f"🔍 Grid Search: Testing {total_combinations} combinations...")
        
        # Test each combination
        results = []
        
        # Process in batches for parallelization
        for i in range(0, total_combinations, max_parallel):
            batch = combinations[i:i + max_parallel]
            batch_params = [
                dict(zip(param_names, combo)) for combo in batch
            ]
            
            # Create configs for this batch
            tasks = []
            for params in batch_params:
                config = self._create_config_from_params(
                    strategy_name,
                    params,
                    param_names,
                    param_is_strategy
                )
                
                task = self.backtest_service.run_backtest(
                    symbol=symbol,
                    strategy_name=strategy_name,
                    days=days,
                    config=config
                )
                tasks.append((params, task))
            
            # Execute batch
            batch_results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            # Store results
            for (params, _), result in zip(tasks, batch_results):
                if isinstance(result, Exception):
                    # Log failed backtest (optional: could store for debugging)
                    continue
                elif isinstance(result, BacktestResult):
                    metric_value = self._get_metric_value(result, optimization_metric)
                    # Only include results with valid trades
                    if result.total_trades > 0:
                        results.append({
                            "parameters": params,
                            "metric_value": metric_value,
                            "result": result,
                            "total_return": result.total_return,
                            "total_trades": result.total_trades,
                            "win_rate": result.win_rate
                        })
            
            # Progress update
            completed = min(i + max_parallel, total_combinations)
            print(f"   Progress: {completed}/{total_combinations} combinations tested")
        
        # Sort by metric value
        results.sort(key=lambda x: x['metric_value'], reverse=True)
        
        # Check if we have any valid results
        if not results:
            optimization_time = time.time() - start_time
            raise ValueError(
                f"Optimization failed: No valid backtest results were generated. "
                f"All {total_combinations} combinations either failed or returned no trades. "
                f"This usually happens when:\n"
                f"1. The backtest period is too short (current: {days} days)\n"
                f"2. Parameter ranges are too restrictive (no signals generated)\n"
                f"3. Symbol '{symbol}' has insufficient data\n\n"
                f"Suggestions:\n"
                f"- Increase 'days' parameter (try 730 or 1095)\n"
                f"- Widen parameter ranges (e.g., RSI threshold: 20-45)\n"
                f"- Try a different symbol with more trading history"
            )
        
        print(f"✅ Optimization complete: {len(results)} valid configurations found")
        print(f"📊 Best {optimization_metric}: {results[0]['metric_value']:.2f}")
        print(f"⚙️  Best parameters: {results[0]['parameters']}")
        
        # Get best configuration
        best = results[0]
        best_config = self._create_config_from_params(
            strategy_name,
            best['parameters'],
            param_names,
            param_is_strategy
        )
        
        # Prepare top results
        top_10 = [
            {
                "parameters": r['parameters'],
                "metric_value": round(r['metric_value'], 2),
                "total_return": round(r['total_return'], 2),
                "sharpe_ratio": round(r['result'].sharpe_ratio, 2),
                "max_drawdown": round(r['result'].max_drawdown, 2),
                "win_rate": round(r['win_rate'], 2),
                "total_trades": r['total_trades']
            }
            for r in results[:10]
        ]
        
        optimization_time = time.time() - start_time
        
        return OptimizationResult(
            strategy_name=strategy_name,
            symbol=symbol,
            optimization_metric=optimization_metric,
            best_config=best_config.model_dump(),
            best_score=round(best['metric_value'], 2),
            total_combinations=total_combinations,
            top_results=top_10,
            optimization_time=round(optimization_time, 2)
        )
    
    async def walk_forward_analysis(
        self,
        symbol: str,
        strategy_name: str,
        parameter_ranges: List[ParameterRange],
        total_days: int = 730,
        train_pct: float = 0.6,
        optimization_metric: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """
        Perform walk-forward analysis.
        
        Split data into:
        - Training period (60%): Optimize parameters
        - Validation period (20%): Test optimized parameters
        - Test period (20%): Out-of-sample testing
        
        Args:
            symbol: Ticker symbol
            strategy_name: Strategy name
            parameter_ranges: Parameters to optimize
            total_days: Total period
            train_pct: Training period percentage
            optimization_metric: Metric to optimize
            
        Returns:
            Dict with train/validation/test results
        """
        print(f"\n🔄 Walk-Forward Analysis for {symbol}")
        print(f"   Total Period: {total_days} days")
        
        train_days = int(total_days * train_pct)
        remaining_days = total_days - train_days
        val_days = int(remaining_days * 0.5)
        test_days = remaining_days - val_days
        
        print(f"   Train: {train_days} days | Validation: {val_days} days | Test: {test_days} days")
        
        # Step 1: Optimize on training data
        print(f"\n📚 Phase 1: Training (Optimization)")
        train_result = await self.optimize_grid_search(
            symbol=symbol,
            strategy_name=strategy_name,
            parameter_ranges=parameter_ranges,
            days=train_days,
            optimization_metric=optimization_metric
        )
        
        best_config_dict = train_result.best_config
        # Convert dict back to StrategyConfig for backtesting
        from app.strategies.base_strategy import StrategyConfig
        best_config = StrategyConfig(**best_config_dict)
        print(f"   Best config from training: {best_config.parameters}")
        
        # Step 2: Test on validation data
        print(f"\n🧪 Phase 2: Validation (Parameter Testing)")
        val_backtest = await self.backtest_service.run_backtest(
            symbol=symbol,
            strategy_name=strategy_name,
            days=val_days,
            config=best_config
        )
        
        print(f"   Validation {optimization_metric}: {self._get_metric_value(val_backtest, optimization_metric):.2f}")
        
        # Step 3: Test on out-of-sample data
        print(f"\n🎯 Phase 3: Testing (Out-of-Sample)")
        test_backtest = await self.backtest_service.run_backtest(
            symbol=symbol,
            strategy_name=strategy_name,
            days=test_days,
            config=best_config
        )
        
        print(f"   Test {optimization_metric}: {self._get_metric_value(test_backtest, optimization_metric):.2f}")
        
        # Summary
        train_metric = train_result.best_score
        val_metric = self._get_metric_value(val_backtest, optimization_metric)
        test_metric = self._get_metric_value(test_backtest, optimization_metric)
        
        # Check for overfitting
        overfit_score = (train_metric - test_metric) / train_metric * 100 if train_metric != 0 else 0
        
        print(f"\n📊 Summary:")
        print(f"   Train {optimization_metric}: {train_metric:.2f}")
        print(f"   Validation {optimization_metric}: {val_metric:.2f}")
        print(f"   Test {optimization_metric}: {test_metric:.2f}")
        print(f"   Overfitting: {overfit_score:.1f}% degradation")
        
        if overfit_score > 30:
            print(f"   ⚠️  Warning: Potential overfitting detected!")
        elif overfit_score < 10:
            print(f"   ✅ Good: Low overfitting, strategy is robust")
        
        return {
            "symbol": symbol,
            "strategy_name": strategy_name,
            "best_config": best_config.model_dump(),
            "train": {
                "days": train_days,
                "metric": round(train_metric, 2),
                "optimization_result": train_result
            },
            "validation": {
                "days": val_days,
                "metric": round(val_metric, 2),
                "backtest_result": val_backtest
            },
            "test": {
                "days": test_days,
                "metric": round(test_metric, 2),
                "backtest_result": test_backtest
            },
            "overfitting_score": round(overfit_score, 2)
        }
    
    def _create_config_from_params(
        self,
        strategy_name: str,
        params: Dict[str, Any],
        param_names: List[str],
        param_is_strategy: List[bool]
    ) -> StrategyConfig:
        """Create StrategyConfig from parameter dict"""
        # Get default config
        default_config = StrategyFactory.get_strategy_info(strategy_name)
        
        # Update with new parameters
        strategy_params = default_config.get('parameters', {})
        
        for name, value in params.items():
            idx = param_names.index(name)
            if param_is_strategy[idx]:
                strategy_params[name] = value
            else:
                default_config[name] = value
        
        return StrategyConfig(
            name=strategy_name,
            holding_days=params.get('holding_days', default_config['holding_days']),
            stop_loss_pct=params.get('stop_loss_pct', default_config['stop_loss_pct']),
            take_profit_pct=params.get('take_profit_pct', default_config['take_profit_pct']),
            parameters=strategy_params
        )
    
    def _get_metric_value(self, result: BacktestResult, metric_name: str) -> float:
        """Extract metric value from backtest result"""
        metric_map = {
            "sharpe_ratio": result.sharpe_ratio,
            "sortino_ratio": result.sortino_ratio,
            "total_return": result.total_return,
            "profit_factor": result.profit_factor,
            "win_rate": result.win_rate,
            "alpha": result.alpha,
            "expectancy": result.expectancy
        }
        return metric_map.get(metric_name, result.sharpe_ratio)
    
    def get_default_ranges(self, strategy_name: str) -> List[ParameterRange]:
        """
        Get sensible default parameter ranges for a strategy.
        
        Args:
            strategy_name: Strategy name
            
        Returns:
            List of ParameterRange objects
        """
        ranges = {
            "buy_the_dip": [
                ParameterRange("ema_length", [100, 150, 200, 250], True),
                ParameterRange("rsi_threshold", [25, 30, 35, 40], True),
                ParameterRange("holding_days", [3, 5, 7, 10], False),
                ParameterRange("stop_loss_pct", [3, 5, 7], False),
            ],
            "mean_reversion": [
                ParameterRange("bb_length", [15, 20, 25, 30], True),
                ParameterRange("bb_std", [1.5, 2.0, 2.5], True),
                ParameterRange("rsi_threshold", [25, 30, 35], True),
                ParameterRange("holding_days", [3, 5, 7], False),
            ],
            "momentum": [
                ParameterRange("short_ema", [8, 12, 16], True),
                ParameterRange("long_ema", [21, 26, 32], True),
                ParameterRange("rsi_threshold", [45, 50, 55], True),
                ParameterRange("holding_days", [7, 10, 14], False),
            ]
        }
        
        return ranges.get(strategy_name, [])
