"""
Technical Analysis Endpoints
- Single Symbol Technical Analysis (Trend, RSI, Signals)
- Market Scanner (Multiple symbols with filters)
- Backtesting with Strategy Pattern
- Portfolio Backtesting
- Parameter Optimization
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from app.core.dependencies import (
    get_technical_analysis_service, 
    get_market_scanner_service,
    get_backtest_service,
    get_portfolio_backtest_service,
    get_optimization_service
)
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.market_scanner_service import MarketScannerService
from app.services.backtest_service import BacktestService
from app.services.portfolio_backtest_service import PortfolioBacktestService
from app.services.optimization_service import ParameterOptimizationService, ParameterRange
from app.strategies.base_strategy import StrategyConfig
from app.models.backtest import (
    BacktestResult, 
    PortfolioBacktestResult,
    OptimizationResult,
    TransactionCosts,
    PositionSizing
)
from app.models.market_data import TechnicalAnalysisResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Preset ง่ายๆ สำหรับทดสอบ (ของจริงควรอยู่ใน Database หรือ Config)
PRESETS = {
    "CRYPTO_TOP": ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"],
    "TECH_GIANTS": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]
}


# ============================================================================
# SINGLE SYMBOL ANALYSIS
# ============================================================================

@router.get("/{symbol}", response_model=TechnicalAnalysisResult)
async def get_technical_analysis(
    symbol: str,
    service: TechnicalAnalysisService = Depends(get_technical_analysis_service)
):
    """
    Get technical analysis summary (Trend, RSI, Signals) for a given symbol.
    """
    logger.info(f"Requesting technical analysis for symbol: {symbol}")
    try:
        result = await service.analyze(symbol)
        logger.info(f"Technical analysis completed successfully for {symbol}")
        return result
    except ValueError as e:
        logger.warning(f"Symbol not found: {symbol} - {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MARKET SCANNER
# ============================================================================

@router.post("/scan", response_model=List[TechnicalAnalysisResult])
async def scan_market(
    symbols: Optional[List[str]] = Body(None, description="Custom list of symbols"),
    preset: Optional[str] = Query(None, description="Use preset list: CRYPTO_TOP, TECH_GIANTS"),
    signal_filter: Optional[str] = Query(None, description="Filter by signal: BUY_DIP, SELL_RALLY"),
    service: MarketScannerService = Depends(get_market_scanner_service)
):
    """
    Scan a list of assets to find trading signals.
    """
    logger.info(f"Starting market scan - preset: {preset}, signal_filter: {signal_filter}")
    
    try:
        target_symbols = []
        default_preset = "TECH_GIANTS"
        
        # 1. Determine list of symbols
        if symbols:
            target_symbols = symbols
            logger.info(f"Using custom symbols: {symbols}")
        elif preset and preset in PRESETS:
            target_symbols = PRESETS[preset]
            logger.info(f"Using preset '{preset}' with {len(target_symbols)} symbols")
        else:
            # Default ถ้าไม่ส่งอะไรมาเลย
            target_symbols = PRESETS[default_preset]
            logger.info(f"Using default preset '{default_preset}' with {len(target_symbols)} symbols")

        if not target_symbols:
            logger.warning("No symbols to scan")
            raise HTTPException(status_code=400, detail="No symbols provided for scanning")

        # 2. Execute Scan
        logger.info(f"Scanning {len(target_symbols)} symbols: {target_symbols}")
        results = await service.scan(target_symbols, filter_signal=signal_filter)
        
        logger.info(f"Market scan completed successfully. Found {len(results)} results")
        return results
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid input for market scan: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during market scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Market scan failed: {str(e)}")
    
# ============================================================================
# BACKTESTING WITH STRATEGY PATTERN
# ============================================================================

@router.get("/strategies", tags=["Backtest"])
async def list_strategies(
    service: BacktestService = Depends(get_backtest_service)
):
    """
    List all available trading strategies.
    
    Returns:
        List of strategy names and their default configurations
    """
    try:
        strategies = await service.get_available_strategies()
        
        # Get info for each strategy
        strategy_info = {}
        for name in strategies:
            info = await service.get_strategy_info(name)
            strategy_info[name] = info
        
        return {
            "available_strategies": strategies,
            "strategy_details": strategy_info
        }
    except Exception as e:
        logger.error(f"Error listing strategies: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest/{symbol}", response_model=BacktestResult, tags=["Backtest"])
async def backtest_strategy(
    symbol: str,
    strategy: str = Query("buy_the_dip", description="Strategy name (buy_the_dip, mean_reversion, momentum)"),
    days: int = Query(365, ge=30, le=1000, description="Number of days to backtest"),
    service: BacktestService = Depends(get_backtest_service)
):
    """
    Backtest a trading strategy on historical data.
    
    **Available Strategies:**
    - `buy_the_dip`: Trend following + RSI pullback
    - `mean_reversion`: Bollinger Bands mean reversion  
    - `momentum`: EMA crossover + momentum confirmation
    
    **Parameters:**
    - **symbol**: Stock/Crypto ticker (e.g., AAPL, BTC-USD)
    - **strategy**: Strategy name (default: buy_the_dip)
    - **days**: Historical days to test (default: 365)
    
    **Returns:**
    - Win rate, average return, Sharpe ratio
    - Maximum drawdown, profit factor
    - Recent trade history
    """
    logger.info(f"🔙 Starting backtest for {symbol} with strategy '{strategy}' over {days} days")
    
    try:
        result = await service.run_backtest(
            symbol=symbol,
            strategy_name=strategy,
            days=days
        )
        
        logger.info(
            f"✅ Backtest completed: {result.total_trades} trades, "
            f"{result.win_rate}% win rate, {result.avg_return}% avg return"
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Backtest validation error for {symbol}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Backtest error for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/{symbol}/custom", response_model=BacktestResult, tags=["Backtest"])
async def backtest_with_custom_config(
    symbol: str,
    strategy_name: str = Query(..., description="Strategy name"),
    config: StrategyConfig = Body(..., description="Custom strategy configuration"),
    days: int = Query(365, ge=30, le=1000, description="Number of days to backtest"),
    service: BacktestService = Depends(get_backtest_service)
):
    """
    Backtest with custom strategy configuration.
    
    This endpoint allows you to customize strategy parameters:
    - Holding days
    - Stop loss / Take profit levels
    - Strategy-specific indicators (RSI threshold, EMA length, etc.)
    
    **Example Request Body:**
    ```json
    {
        "name": "buy_the_dip",
        "holding_days": 7,
        "stop_loss_pct": 3.0,
        "take_profit_pct": 12.0,
        "parameters": {
            "ema_length": 150,
            "rsi_threshold": 30
        }
    }
    ```
    """
    logger.info(
        f"🔙 Starting custom backtest for {symbol} with {strategy_name} "
        f"(holding: {config.holding_days}d, SL: {config.stop_loss_pct}%, TP: {config.take_profit_pct}%)"
    )
    
    try:
        result = await service.run_backtest(
            symbol=symbol,
            strategy_name=strategy_name,
            days=days,
            config=config
        )
        
        logger.info(f"✅ Custom backtest completed for {symbol}")
        return result
        
    except ValueError as e:
        logger.warning(f"Custom backtest validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Custom backtest error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PORTFOLIO BACKTESTING
# ============================================================================

@router.post("/backtest/portfolio", response_model=PortfolioBacktestResult, tags=["Portfolio"])
async def backtest_portfolio(
    symbols: List[str] = Body(..., description="List of symbols to backtest"),
    strategy: str = Query("buy_the_dip", description="Strategy name"),
    days: int = Query(365, ge=30, le=1000, description="Number of days"),
    initial_capital: float = Query(100000.0, description="Initial capital"),
    service: PortfolioBacktestService = Depends(get_portfolio_backtest_service)
):
    """
    Backtest a portfolio of multiple symbols simultaneously.
    
    **Benefits:**
    - Diversification analysis
    - Portfolio-level metrics
    - Correlation analysis
    - Capital allocation
    
    **Example:**
    ```json
    {
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "strategy": "buy_the_dip",
        "days": 365,
        "initial_capital": 100000
    }
    ```
    """
    logger.info(f"📊 Starting portfolio backtest with {len(symbols)} symbols: {symbols}")
    
    try:
        result = await service.run_portfolio_backtest(
            symbols=symbols,
            strategy_name=strategy,
            days=days,
            initial_capital=initial_capital
        )
        
        logger.info(
            f"✅ Portfolio backtest completed: {result.total_return:.2f}% return, "
            f"Sharpe: {result.sharpe_ratio:.2f}"
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Portfolio backtest error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Portfolio backtest error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/compare-strategies", tags=["Portfolio"])
async def compare_strategies(
    symbol: str = Query(..., description="Symbol to test"),
    strategies: List[str] = Body(..., description="List of strategy names"),
    days: int = Query(365, ge=30, le=1000, description="Number of days"),
    service: PortfolioBacktestService = Depends(get_portfolio_backtest_service)
):
    """
    Compare multiple strategies on the same symbol.
    
    **Example:**
    ```json
    {
        "symbol": "AAPL",
        "strategies": ["buy_the_dip", "mean_reversion", "momentum"],
        "days": 365
    }
    ```
    
    **Returns:**
    Dict with each strategy's results for easy comparison.
    """
    logger.info(f"⚖️  Comparing {len(strategies)} strategies on {symbol}")
    
    try:
        results = await service.compare_strategies(
            symbol=symbol,
            strategy_names=strategies,
            days=days
        )
        
        # Summary
        summary = {
            "symbol": symbol,
            "strategies_tested": len(strategies),
            "comparison": {
                name: {
                    "total_return": result.total_return,
                    "sharpe_ratio": result.sharpe_ratio,
                    "win_rate": result.win_rate,
                    "max_drawdown": result.max_drawdown,
                    "total_trades": result.total_trades
                }
                for name, result in results.items()
            },
            "detailed_results": results
        }
        
        logger.info(f"✅ Strategy comparison completed")
        return summary
        
    except Exception as e:
        logger.error(f"Strategy comparison error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PARAMETER OPTIMIZATION
# ============================================================================

@router.post("/optimize/{symbol}", response_model=OptimizationResult, tags=["Optimization"])
async def optimize_parameters(
    symbol: str,
    strategy: str = Query(..., description="Strategy to optimize"),
    days: int = Query(365, ge=30, le=1000, description="Number of days"),
    metric: str = Query("sharpe_ratio", description="Metric to optimize"),
    use_default_ranges: bool = Query(True, description="Use default parameter ranges"),
    service: ParameterOptimizationService = Depends(get_optimization_service)
):
    """
    Find optimal parameters for a strategy using grid search.
    
    **Optimization Metrics:**
    - `sharpe_ratio`: Risk-adjusted returns (recommended)
    - `total_return`: Maximum returns
    - `profit_factor`: Profit/loss ratio
    - `win_rate`: Win percentage
    - `alpha`: Excess return vs buy & hold
    
    **Example:**
    ```
    GET /optimize/AAPL?strategy=buy_the_dip&metric=sharpe_ratio
    ```
    
    **Returns:**
    - Best parameter configuration
    - Top 10 configurations
    - Performance metrics
    """
    logger.info(f"🔍 Optimizing {strategy} for {symbol} on {metric}")
    
    try:
        # Get parameter ranges
        if use_default_ranges:
            param_ranges = service.get_default_ranges(strategy)
        else:
            # Could add custom ranges in request body
            param_ranges = service.get_default_ranges(strategy)
        
        if not param_ranges:
            raise HTTPException(
                status_code=400,
                detail=f"No default parameter ranges for strategy '{strategy}'"
            )
        
        # Run optimization
        result = await service.optimize_grid_search(
            symbol=symbol,
            strategy_name=strategy,
            parameter_ranges=param_ranges,
            days=days,
            optimization_metric=metric,
            max_parallel=3  # Limit to avoid overwhelming the system
        )
        
        logger.info(
            f"✅ Optimization completed: Best {metric} = {result.best_score:.2f}"
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Optimization error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Optimization error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/{symbol}/walk-forward", tags=["Optimization"])
async def walk_forward_analysis(
    symbol: str,
    strategy: str = Query(..., description="Strategy to test"),
    total_days: int = Query(730, ge=365, le=1825, description="Total period (2-5 years)"),
    metric: str = Query("sharpe_ratio", description="Optimization metric"),
    service: ParameterOptimizationService = Depends(get_optimization_service)
):
    """
    Perform walk-forward analysis to test for overfitting.
    
    **Process:**
    1. **Train (60%)**: Optimize parameters
    2. **Validation (20%)**: Test parameters
    3. **Test (20%)**: Out-of-sample validation
    
    **Benefits:**
    - Detects overfitting
    - More realistic performance estimates
    - Validates strategy robustness
    
    **Example:**
    ```
    POST /optimize/AAPL/walk-forward?strategy=buy_the_dip&total_days=730
    ```
    """
    logger.info(f"🔄 Walk-forward analysis for {symbol} ({total_days} days)")
    
    try:
        param_ranges = service.get_default_ranges(strategy)
        
        if not param_ranges:
            raise HTTPException(
                status_code=400,
                detail=f"No default parameter ranges for strategy '{strategy}'"
            )
        
        result = await service.walk_forward_analysis(
            symbol=symbol,
            strategy_name=strategy,
            parameter_ranges=param_ranges,
            total_days=total_days,
            optimization_metric=metric
        )
        
        logger.info(
            f"✅ Walk-forward completed: Overfitting score = {result['overfitting_score']:.1f}%"
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Walk-forward error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Walk-forward error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))