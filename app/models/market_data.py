# app/models/market_data.py
"""
Pydantic models for market data responses.
These models provide type safety and validation for data returned from providers.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date as date_type


class TranscriptResponse(BaseModel):
    """Earnings call transcript response from data providers"""
    date: str = Field(..., description="Date of the earnings call (YYYY-MM-DD format)")
    content: str = Field(..., description="Full transcript text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-10-25",
                "content": "Apple Inc. Q4 2024 Earnings Call Transcript..."
            }
        }


class FinancialMetrics(BaseModel):
    """Financial metrics for a company"""
    # Valuation ratios
    peRatioTTM: Optional[float] = Field(None, description="Price to Earnings ratio (TTM)")
    pbRatioTTM: Optional[float] = Field(None, description="Price to Book ratio (TTM)")
    
    # Per share metrics
    netIncomePerShareTTM: Optional[float] = Field(None, description="Earnings per share (TTM)")
    bookValuePerShareTTM: Optional[float] = Field(None, description="Book value per share (TTM)")
    revenuePerShareTTM: Optional[float] = Field(None, description="Revenue per share (TTM)")
    
    # Other metrics
    dividendYieldTTM: Optional[float] = Field(None, description="Dividend yield (TTM)")
    marketCapTTM: Optional[float] = Field(None, description="Market capitalization")
    debtToEquityTTM: Optional[float] = Field(None, description="Debt to equity ratio")
    returnOnEquityTTM: Optional[float] = Field(None, description="Return on equity")
    
    class Config:
        # Allow extra fields from API
        extra = "allow"


class CashFlowStatement(BaseModel):
    """Cash flow data for a specific period"""
    date: str = Field(..., description="Period date")
    freeCashFlow: Optional[float] = Field(None, description="Free cash flow for the period")
    
    class Config:
        # Allow extra fields that might come from different providers
        extra = "allow"


class FinancialMetricsResponse(BaseModel):
    """Complete financial metrics response including metrics, price, and cash flows"""
    metrics: FinancialMetrics = Field(..., description="Key financial metrics")
    price: float = Field(..., description="Current stock price")
    cash_flows: List[CashFlowStatement] = Field(
        default_factory=list, 
        description="Historical cash flow statements"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "metrics": {
                    "peRatioTTM": 28.5,
                    "pbRatioTTM": 45.2,
                    "netIncomePerShareTTM": 6.42
                },
                "price": 182.50,
                "cash_flows": [
                    {"date": "2024-09-30", "freeCashFlow": 26850000000}
                ]
            }
        }


class PeerListResponse(BaseModel):
    """List of peer company ticker symbols"""
    peers: List[str] = Field(
        default_factory=list,
        description="List of peer company ticker symbols"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "peers": ["MSFT", "GOOGL", "META", "AMZN", "NVDA"]
            }
        }
