import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.backtest_service import BacktestService
from app.strategies.buy_the_dip_strategy import BuyTheDipStrategy
from app.strategies.base_strategy import StrategyConfig
from app.models.backtest import TransactionCosts, PositionSizing, BacktestResult
from app.data_sources.base import DataSourceProvider
from app.models.market_data import PriceCandle

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_data_provider():
    provider = MagicMock(spec=DataSourceProvider)
    provider.get_historical_prices = AsyncMock(return_value=[])
    return provider

@pytest.fixture
def basic_strategy_config():
    return StrategyConfig(
        name="buy_the_dip",
        holding_days=5,
        stop_loss_pct=5.0,
        take_profit_pct=10.0,
        parameters={
            "ema_length": 5,  # Short for testing
            "rsi_length": 2,  # Short for testing
            "rsi_threshold": 30
        }
    )

@pytest.fixture
def sample_df():
    """
    Create a synthetic DataFrame for testing.
    Pattern:
    - Days 0-4: Flat/Uptrend to establish EMA
    - Day 5: Dip (RSI < 30) -> Signal should be generated here (at Close)
    - Day 6: Entry Day (Open)
    - Day 7: Normal movement
    - Day 8: Big pump (High > TP) -> Should exit here
    """
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(20)]
    
    data = {
        'open':  [100.0] * 20,
        'high':  [105.0] * 20,
        'low':   [95.0]  * 20,
        'close': [100.0] * 20,
        'volume': [1000] * 20
    }
    
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'timestamp'
    
    # Manipulate for Strategy Signals
    # 1. Establish Uptrend (Price > EMA)
    # We set price high enough so EMA is below price
    df.loc[dates[0]:dates[4], 'close'] = 110.0 
    
    # 2. Create Dip (RSI Oversold) on Day 5
    # Drop price sharply to trigger RSI drop, but keep it above EMA if possible
    # Or just force the indicators in the test if we want to test Service logic only.
    # But here let's try to test Strategy logic too.
    
    return df

# ============================================================================
# Strategy Tests
# ============================================================================

def test_buy_the_dip_exit_logic(basic_strategy_config):
    strategy = BuyTheDipStrategy(basic_strategy_config)
    
    entry_price = 100.0
    
    # 1. Normal Hold
    should_exit, reason = strategy.check_exit_conditions(
        entry_price, current_close=102.0, current_low=99.0, current_high=103.0
    )
    assert not should_exit
    assert reason == "HOLDING"
    
    # 2. Stop Loss Hit (SL = 5% -> 95.0)
    # Case: Low drops to 94.0
    should_exit, reason = strategy.check_exit_conditions(
        entry_price, current_close=98.0, current_low=94.0, current_high=101.0
    )
    assert should_exit
    assert reason == "STOP_LOSS"
    
    # 3. Take Profit Hit (TP = 10% -> 110.0)
    # Case: High reaches 111.0
    should_exit, reason = strategy.check_exit_conditions(
        entry_price, current_close=105.0, current_low=99.0, current_high=111.0
    )
    assert should_exit
    assert reason == "TAKE_PROFIT"

# ============================================================================
# Backtest Service Tests (Realistic Simulation)
# ============================================================================

def test_simulation_entry_execution(mock_data_provider, basic_strategy_config):
    """
    Test that trade is entered on the NEXT DAY Open after signal.
    """
    service = BacktestService(
        data_provider=mock_data_provider,
        transaction_costs=TransactionCosts(commission_pct=0, slippage_pct=0),
        position_sizing=PositionSizing(initial_capital=10000)
    )
    
    # Create minimal DF
    dates = [datetime(2024, 1, i) for i in range(1, 6)]
    df = pd.DataFrame({
        'open': [100, 100, 102, 105, 110],
        'high': [105, 105, 105, 115, 115],
        'low':  [95,  95,  95,  95,  100],
        'close':[100, 100, 100, 110, 110],
        'Signal': [False, True, False, False, False] # Signal on Day 2 (Jan 2)
    }, index=dates)
    
    # Strategy Mock
    strategy = BuyTheDipStrategy(basic_strategy_config)
    
    # Run Simulation
    trades, final_capital = service._simulate_trades_realistic(df, strategy, 10000.0)
    
    assert len(trades) == 1
    trade = trades[0]
    
    # Signal on Jan 2 (Day 2) -> Entry should be Jan 3 (Day 3) Open
    assert trade['entry_date'] == dates[2] # Jan 3
    assert trade['entry_price'] == 102.0   # Open of Jan 3
    
def test_simulation_intraday_exit_tp(mock_data_provider, basic_strategy_config):
    """
    Test that trade exits on the SAME DAY if High hits TP.
    """
    service = BacktestService(
        data_provider=mock_data_provider,
        transaction_costs=TransactionCosts(commission_pct=0, slippage_pct=0),
        position_sizing=PositionSizing(initial_capital=10000)
    )
    
    # Setup:
    # Day 1: Signal
    # Day 2: Entry at Open (100). TP = +10% = 110.
    # Day 2: High reaches 112 -> Should exit immediately at 110 (TP price).
    
    dates = [datetime(2024, 1, i) for i in range(1, 5)]
    df = pd.DataFrame({
        'open':   [100, 100, 100, 100],
        'high':   [100, 112, 100, 100], # Day 2 High hits TP
        'low':    [90,  98,  90,  90],  # Day 2 Low 98 (Above SL 95)
        'close':  [100, 105, 100, 100],
        'Signal': [True, False, False, False] # Signal Day 1
    }, index=dates)
    
    strategy = BuyTheDipStrategy(basic_strategy_config)
    
    trades, _ = service._simulate_trades_realistic(df, strategy, 10000.0)
    
    assert len(trades) == 1
    trade = trades[0]
    
    # Entry Day 2
    assert trade['entry_date'] == dates[1]
    assert trade['entry_price'] == 100.0
    
    # Exit Day 2 (Intraday)
    assert trade['exit_date'] == dates[1]
    assert trade['exit_price'] == pytest.approx(110.0) # TP Price
    assert trade['exit_reason'] == "TAKE_PROFIT"

def test_simulation_gap_down_sl(mock_data_provider, basic_strategy_config):
    """
    Test Gap Down scenario: Open is below SL. Should exit at Open.
    """
    service = BacktestService(
        data_provider=mock_data_provider,
        transaction_costs=TransactionCosts(commission_pct=0, slippage_pct=0),
        position_sizing=PositionSizing(initial_capital=10000)
    )
    
    # Setup:
    # Day 1: Signal
    # Day 2: Entry at 100. SL = -5% = 95.
    # Day 3: Open at 90 (Gap Down below 95).
    
    dates = [datetime(2024, 1, i) for i in range(1, 5)]
    df = pd.DataFrame({
        'open':   [100, 100, 90,  100], # Day 3 Open 90
        'high':   [100, 105, 92,  100],
        'low':    [90,  98,  80,  90],
        'close':  [100, 100, 85,  100],
        'Signal': [True, False, False, False]
    }, index=dates)
    
    strategy = BuyTheDipStrategy(basic_strategy_config)
    
    trades, _ = service._simulate_trades_realistic(df, strategy, 10000.0)
    
    assert len(trades) == 1
    trade = trades[0]
    
    # Entry Day 2
    assert trade['entry_date'] == dates[1]
    assert trade['entry_price'] == 100.0
    
    # Exit Day 3
    assert trade['exit_date'] == dates[2]
    assert trade['exit_price'] == 90.0 # Open Price (worse than SL)
    assert trade['exit_reason'] == "STOP_LOSS"

def test_buy_the_dip_signal_generation(basic_strategy_config):
    """
    Test that the strategy correctly calculates indicators and generates signals.
    """
    strategy = BuyTheDipStrategy(basic_strategy_config)
    
    # 1. Test Indicator Calculation (Integration with pandas_ta)
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(20)]
    df = pd.DataFrame({
        'open': [100.0] * 20,
        'high': [105.0] * 20,
        'low': [95.0] * 20,
        'close': [100.0] * 20,
        'volume': [1000] * 20
    }, index=dates)
    
    # We just want to see if columns are added, not their values (pandas_ta is tested elsewhere)
    df_indicators = strategy.calculate_indicators(df.copy())
    assert 'EMA' in df_indicators.columns
    assert 'RSI' in df_indicators.columns
    
    # 2. Test Signal Logic (Isolated)
    # Create a controlled DataFrame with pre-calculated indicators
    df_controlled = pd.DataFrame({
        'close': [100.0] * 5,
        'EMA': [90.0] * 5, # Price > EMA -> Uptrend
        'RSI': [40, 35, 25, 20, 35] # Cross under 30 at index 2
    }, index=dates[:5])
    
    # Set threshold to 30 for this test
    strategy.config.parameters['rsi_threshold'] = 30
    
    df_signals = strategy.generate_signals(df_controlled.copy())
    
    assert 'Signal' in df_signals.columns
    
    # Index 0: RSI 40 (No signal)
    assert df_signals.iloc[0]['Signal'] == False
    
    # Index 1: RSI 35 (No signal)
    assert df_signals.iloc[1]['Signal'] == False
    
    # Index 2: RSI 25 (Prev 35) -> CROSS UNDER! -> Signal True
    assert df_signals.iloc[2]['Signal'] == True
    
    # Index 3: RSI 20 (Prev 25) -> Already under -> Signal False (No cross)
    assert df_signals.iloc[3]['Signal'] == False
    
    # Index 4: RSI 35 (Prev 20) -> Cross OVER -> Signal False
    assert df_signals.iloc[4]['Signal'] == False

@pytest.mark.asyncio
async def test_run_backtest_full_flow(mock_data_provider, basic_strategy_config):
    """
    Test the full run_backtest flow including data fetching and result construction.
    """
    service = BacktestService(
        data_provider=mock_data_provider,
        transaction_costs=TransactionCosts(commission_pct=0.1, slippage_pct=0.05),
        position_sizing=PositionSizing(initial_capital=10000)
    )
    
    # 1. Setup Mock Data (PriceCandle objects)
    # Create data that triggers a trade: Uptrend -> Dip -> Recovery
    # We need Price > EMA AND RSI < 30.
    # To ensure Price > EMA during a dip, we need a slower EMA (lagging).
    # We'll override config to use EMA(20).
    
    # Override config for this test
    config_dict = basic_strategy_config.model_dump()
    config_dict['parameters']['ema_length'] = 20
    
    # Need enough data for warm-up (20 days) + backtest period (45 days)
    # Let's generate 70 days
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(70)]
    candles = []
    
    # Steady Uptrend: +5 per day for 60 days
    # Prices: 100, 105, ... 400
    prices = [100.0 + i*5 for i in range(61)] 
    
    # Day 61: Dip to 380 (from 400). Drop 20.
    # EMA(20) of [305...400] ~ 350.
    # Price 380 > EMA 350. Uptrend OK.
    prices.append(380.0)
    
    # Day 62-69: Recovery
    prices.extend([385.0 + i*5 for i in range(8)])
    
    for i, date in enumerate(dates):
        price = prices[i]
        candles.append(PriceCandle(
            timestamp=date,
            open=price,
            high=price + 5,
            low=price - 5,
            close=price,
            volume=1000
        ))
        
    mock_data_provider.get_historical_prices.return_value = candles
    
    # 2. Run Backtest
    result = await service.run_backtest(
        symbol="AAPL",
        strategy_name="buy_the_dip",
        days=45, 
        config=config_dict,
        initial_capital=10000.0
    )
    
    # 3. Assertions - Check Completeness of Result
    assert isinstance(result, BacktestResult)
    
    # Metadata
    assert result.symbol == "AAPL"
    assert result.strategy_name == "buy_the_dip"
    assert result.period_days == 45
    assert result.start_date is not None
    assert result.end_date is not None
    
    # Capital & Returns
    assert result.initial_capital == 10000.0
    assert isinstance(result.final_capital, float)
    assert isinstance(result.net_profit, float)
    assert isinstance(result.total_return, float)
    assert isinstance(result.buy_and_hold_return, float)
    assert isinstance(result.alpha, float)
    
    # Trade Metrics
    # We expect at least 1 trade because of the dip
    assert result.total_trades > 0 
    assert 0.0 <= result.win_rate <= 100.0
    assert isinstance(result.profit_factor, float)
    assert isinstance(result.expectancy, float)
    assert isinstance(result.max_drawdown, float)
    assert isinstance(result.max_drawdown_duration, int)
    assert isinstance(result.sharpe_ratio, float)
    assert isinstance(result.sortino_ratio, float)
    
    # Costs
    assert result.total_transaction_costs > 0.0 # We set commission/slippage > 0
    assert result.avg_cost_per_trade > 0.0
    
    # Data Structures
    assert len(result.price_data) == 45
    assert len(result.recent_trades) == result.total_trades
    assert len(result.trade_markers) > 0
    
    # Check content of a trade record
    trade = result.recent_trades[0]
    assert trade.entry_price > 0
    assert trade.exit_price > 0
    assert trade.shares > 0
    assert trade.transaction_costs > 0
    assert trade.exit_reason in ["STOP_LOSS", "TAKE_PROFIT", "TIME_BASED", "END_OF_DATA", "HOLDING"]
    
    # Check if metrics are calculated (even if 0 trades)
    assert result.total_trades >= 0
    assert result.net_profit is not None


