# app/data_sources/mock_provider.py
from datetime import datetime
from app.data_sources.base import DataSourceProvider
from app.models.market_data import (
    TranscriptResponse,
    FinancialMetricsResponse,
    FinancialMetrics,
    CashFlowStatement,
    PeerListResponse
)
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class MockProvider(DataSourceProvider):
    """
    Mock data provider for testing and demonstrations.
    Returns realistic-looking fake data without making any API calls.
    """
    
    def __init__(self):
        self._mock_symbols = ["AAPL", "MSFT", "TSLA"]
    
    @property
    def name(self) -> str:
        return "Mock"
    
    async def get_transcript(self, symbol: str, quarter: int, year: int) -> TranscriptResponse:
        """Return mock transcript data"""
        logger.info(f"[{self.name}] Returning mock transcript for {symbol} Q{quarter} {year}")
        
        # Predefined mock transcripts
        if symbol == "AAPL":
            return TranscriptResponse(
                date="2024-11-01",
                content="""Apple Inc. Q4 2024 Earnings Call Transcript

Tim Cook - CEO:
Good afternoon and thank you for joining us. I'm pleased to report that we had a strong quarter with record revenue of $89.5 billion, up 6% year over year. Our iPhone business continues to show strength with the iPhone 15 family performing exceptionally well.

Luca Maestri - CFO:
Thank you, Tim. Our gross margin expanded to 45.2%, and we returned $25 billion to shareholders through dividends and share buybacks. We're very pleased with our financial performance and the strength of our ecosystem.

Q&A Session:
Analyst: Can you talk about your AI strategy?
Tim Cook: We're very excited about AI and have been integrating it across our products for years. You'll see more innovation in this space in the coming quarters.

Analyst: What about Mac sales?
Tim Cook: Mac had a great quarter with the M3 chip driving strong demand. We're seeing particular strength in the enterprise segment.
"""
            )
        
        # Generic mock data for unknown symbols
        return TranscriptResponse(
            date=f"{year}-{quarter * 3:02d}-15",
            content=f"""Mock Earnings Call Transcript for {symbol}

CEO: Thank you for joining us today. We had a solid quarter with good performance across our key metrics.

CFO: Our revenue grew year over year, and we maintained healthy margins. We're optimistic about the future.

Q&A Session:
Analyst: What are your growth prospects?
CEO: We see significant opportunities in our core markets and are investing in innovation.

Analyst: Any concerns about the macroeconomic environment?
CFO: We're monitoring conditions closely but remain confident in our strategy.

This is mock data for testing purposes.
"""
        )
    
    async def get_financial_metrics(self, symbol: str, limit: int = 5) -> FinancialMetricsResponse:
        """Return mock financial metrics"""
        logger.info(f"[{self.name}] Returning mock financial metrics for {symbol}")
        
        # Predefined mock data for common symbols
        mock_data = {
            "AAPL": {
                "metrics": FinancialMetrics(
                    peRatioTTM=28.5,
                    pbRatioTTM=45.2,
                    netIncomePerShareTTM=6.42,
                    bookValuePerShareTTM=4.25,
                    dividendYieldTTM=0.0045,
                    marketCapTTM=2850000000000,
                    debtToEquityTTM=1.85,
                    returnOnEquityTTM=1.52,
                    revenuePerShareTTM=24.32
                ),
                "price": 182.50,
                "cash_flows": [
                    CashFlowStatement(date="2024-09-30", freeCashFlow=26850000000),
                    CashFlowStatement(date="2023-09-30", freeCashFlow=25320000000),
                    CashFlowStatement(date="2022-09-30", freeCashFlow=24180000000),
                    CashFlowStatement(date="2021-09-30", freeCashFlow=22450000000),
                    CashFlowStatement(date="2020-09-30", freeCashFlow=20980000000)
                ]
            },
            "MSFT": {
                "metrics": FinancialMetrics(
                    peRatioTTM=32.8,
                    pbRatioTTM=12.5,
                    netIncomePerShareTTM=11.86,
                    bookValuePerShareTTM=31.42,
                    dividendYieldTTM=0.0072,
                    marketCapTTM=3100000000000,
                    debtToEquityTTM=0.45,
                    returnOnEquityTTM=0.42,
                    revenuePerShareTTM=75.28
                ),
                "price": 388.00,
                "cash_flows": [
                    CashFlowStatement(date="2024-06-30", freeCashFlow=21850000000),
                    CashFlowStatement(date="2023-06-30", freeCashFlow=19320000000),
                    CashFlowStatement(date="2022-06-30", freeCashFlow=17580000000),
                    CashFlowStatement(date="2021-06-30", freeCashFlow=16250000000),
                    CashFlowStatement(date="2020-06-30", freeCashFlow=14920000000)
                ]
            },
            "TSLA": {
                "metrics": FinancialMetrics(
                    peRatioTTM=65.2,
                    pbRatioTTM=12.8,
                    netIncomePerShareTTM=3.25,
                    bookValuePerShareTTM=19.45,
                    dividendYieldTTM=0.0,
                    marketCapTTM=685000000000,
                    debtToEquityTTM=0.18,
                    returnOnEquityTTM=0.22,
                    revenuePerShareTTM=82.15
                ),
                "price": 245.75,
                "cash_flows": [
                    CashFlowStatement(date="2024-09-30", freeCashFlow=2750000000),
                    CashFlowStatement(date="2023-09-30", freeCashFlow=2450000000),
                    CashFlowStatement(date="2022-09-30", freeCashFlow=2180000000),
                    CashFlowStatement(date="2021-09-30", freeCashFlow=1850000000),
                    CashFlowStatement(date="2020-09-30", freeCashFlow=1520000000)
                ]
            }
        }
        
        # Return predefined data if available
        if symbol in mock_data:
            data = mock_data[symbol]
            return FinancialMetricsResponse(
                metrics=data["metrics"],
                price=data["price"],
                cash_flows=data["cash_flows"][:limit]
            )
        
        # Generic mock data for unknown symbols
        cash_flows = [
            CashFlowStatement(
                date=f"{2024-i}-12-31",
                freeCashFlow=5000000000 * (1.1 ** i)
            )
            for i in range(limit)
        ]
        
        return FinancialMetricsResponse(
            metrics=FinancialMetrics(
                peRatioTTM=25.0,
                pbRatioTTM=3.5,
                netIncomePerShareTTM=5.00,
                bookValuePerShareTTM=35.00,
                dividendYieldTTM=0.02,
                marketCapTTM=100000000000,
                debtToEquityTTM=0.50,
                returnOnEquityTTM=0.15,
                revenuePerShareTTM=50.00
            ),
            price=125.00,
            cash_flows=cash_flows
        )
    
    async def get_peers(self, symbol: str) -> PeerListResponse:
        """Return mock peer list"""
        logger.info(f"[{self.name}] Returning mock peers for {symbol}")
        
        # Predefined peers
        mock_peers = {
            "AAPL": ["MSFT", "GOOGL", "META", "AMZN", "NVDA"],
            "MSFT": ["AAPL", "GOOGL", "AMZN", "ORCL", "CRM"],
            "TSLA": ["F", "GM", "RIVN", "LCID", "NIO"]
        }
        
        # Return predefined peers if available
        if symbol in mock_peers:
            return PeerListResponse(peers=mock_peers[symbol])
        
        # Generic mock peers
        return PeerListResponse(peers=["PEER1", "PEER2", "PEER3", "PEER4", "PEER5"])
