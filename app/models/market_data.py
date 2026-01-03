# app/models/market_data.py
"""
Pydantic models for market data responses.
These models provide type safety and validation for data returned from providers.
"""
import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date as date_type, datetime

class SearchSymbolResponse(BaseModel):
    """Response model for symbol search results"""
    symbols: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Full company name")
    currency: str = Field(..., description="Trading currency")
    exchange: str = Field(..., description="Stock exchange short name")
    exchangeFullName: str = Field(..., description="Full name of the stock exchange")

    class config:
        json_schema_extra = {
            "example": {
                "symbols": "AAPL",
                "name": "Apple Inc.",
                "currency": "USD",
                "exchange": "NASDAQ",
                "exchangeFullName": "NASDAQ Stock Market"
            }
        }

class CentralIndexKeyResponse(BaseModel):
    """Response model for CIK lookup results"""
    symbols: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Full company name")
    cik: str = Field(..., description="Central Index Key")
    currency: str = Field(..., description="Trading currency")
    exchange: str = Field(..., description="Stock exchange short name")
    exchangeFullName: str = Field(..., description="Full name of the stock exchange")

    class config:
        json_schema_extra = {
            "example": {
                "symbols": "AAPL",
                "name": "Apple Inc.",
                "cik": "0000320193",
                "currency": "USD",
                "exchange": "NASDAQ",
                "exchangeFullName": "NASDAQ Stock Market"
            }
        }

class CUSIPResponse(BaseModel):
    """Response model for CUSIP lookup results"""
    symbol: str = Field(..., description="Stock ticker symbol")
    companyName: str = Field(..., description="Full company name")
    cusip: str = Field(..., description="CUSIP identifier")
    marketCap: str = Field(..., description="Market capitalization")

    class config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "cusip": "037833100",
                "marketCap": "2.5T"
            }
        }

class InternationalSecurityIdentifierNumberResponse(BaseModel):
    """Response model for ISIN lookup results"""
    symbol: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Full company name")
    isin: str = Field(..., description="International Securities Identification Number")
    marketCap: str = Field(..., description="Market capitalization")

    class config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "isin": "US0378331005",
                "marketCap": "2.5T"
            }
        }

class CompanyScreenerResponse(BaseModel):
    """Response model for company screener results"""
    symbol: str = Field(..., description="Stock ticker symbol")
    companyName: str = Field(..., description="Full company name")
    marketCap: float = Field(..., description="Market capitalization")
    sector: str = Field(..., description="Company sector")
    industry: str = Field(..., description="Company industry")
    beta: float = Field(..., description="Beta coefficient")
    price: float = Field(..., description="Current stock price")
    lastAnnualDividend: float = Field(..., description="Last annual dividend")
    volume: int = Field(..., description="Trading volume")
    exchange: str = Field(..., description="Full exchange name")
    exchangeShortName: str = Field(..., description="Exchange short name")
    country: str = Field(..., description="Country code")
    isEtf: bool = Field(..., description="Whether the security is an ETF")
    isFund: bool = Field(..., description="Whether the security is a fund")
    isActivelyTrading: bool = Field(..., description="Whether the security is actively trading")

    class config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "marketCap": 2500000000000,
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "beta": 1.2,
                "price": 182.50,
                "lastAnnualDividend": 0.88,
                "volume": 75000000,
                "exchange": "NASDAQ Stock Market",
                "exchangeShortName": "NASDAQ",
                "country": "US",
                "isEtf": False,
                "isFund": False,
                "isActivelyTrading": True
            }
        }

class ExchangeVariantsResponse(BaseModel):
    """Response model for exchange variants/company profile data"""
    symbol: str = Field(..., description="Stock ticker symbol")
    price: float = Field(..., description="Current stock price")
    beta: Optional[float] = Field(None, description="Beta coefficient")
    volAvg: Optional[int] = Field(None, description="Average trading volume")
    mktCap: Optional[float] = Field(None, description="Market capitalization")
    lastDiv: Optional[float] = Field(None, description="Last dividend")
    range: Optional[str] = Field(None, description="52-week price range")
    changes: Optional[float] = Field(None, description="Price change")
    companyName: str = Field(..., description="Full company name")
    currency: Optional[str] = Field(None, description="Trading currency")
    cik: Optional[str] = Field(None, description="Central Index Key")
    isin: Optional[str] = Field(None, description="International Securities Identification Number")
    cusip: Optional[str] = Field(None, description="CUSIP identifier")
    exchange: Optional[str] = Field(None, description="Full exchange name")
    exchangeShortName: Optional[str] = Field(None, description="Exchange short name")
    industry: Optional[str] = Field(None, description="Company industry")
    website: Optional[str] = Field(None, description="Company website URL")
    description: Optional[str] = Field(None, description="Company description")
    ceo: Optional[str] = Field(None, description="Chief Executive Officer")
    sector: Optional[str] = Field(None, description="Company sector")
    country: Optional[str] = Field(None, description="Country code")
    fullTimeEmployees: Optional[str] = Field(None, description="Number of full-time employees")
    phone: Optional[str] = Field(None, description="Company phone number")
    address: Optional[str] = Field(None, description="Company address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    zip: Optional[str] = Field(None, description="Postal code")
    dcfDiff: Optional[float] = Field(None, description="DCF difference")
    dcf: Optional[float] = Field(None, description="Discounted cash flow valuation")
    image: Optional[str] = Field(None, description="Company logo image URL")
    ipoDate: Optional[str] = Field(None, description="IPO date (YYYY-MM-DD format)")
    defaultImage: Optional[bool] = Field(None, description="Whether using default image")
    isEtf: Optional[bool] = Field(None, description="Whether the security is an ETF")
    isActivelyTrading: Optional[bool] = Field(None, description="Whether the security is actively trading")
    isAdr: Optional[bool] = Field(None, description="Whether the security is an ADR")
    isFund: Optional[bool] = Field(None, description="Whether the security is a fund")

    class Config:
        json_schema_extra = {
            "example": {
                    "symbol": "AAPL",
                    "price": 225.46,
                    "beta": 1.24,
                    "volAvg": 54722288,
                    "mktCap": 3427916386000,
                    "lastDiv": 1,
                    "range": "164.08-237.23",
                    "changes": -7.54,
                    "companyName": "Apple Inc.",
                    "currency": "USD",
                    "cik": "0000320193",
                    "isin": "US0378331005",
                    "cusip": "037833100",
                    "exchange": "NASDAQ Global Select",
                    "exchangeShortName": "NASDAQ",
                    "industry": "Consumer Electronics",
                    "website": "https://www.apple.com",
                    "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discov...",
                    "ceo": "Mr. Timothy D. Cook",
                    "sector": "Technology",
                    "country": "US",
                    "fullTimeEmployees": "161000",
                    "phone": "408 996 1010",
                    "address": "One Apple Park Way",
                    "city": "Cupertino",
                    "state": "CA",
                    "zip": "95014",
                    "dcfDiff": 62.45842,
                    "dcf": 161.68157666868984,
                    "image": "https://financialmodelingprep.com/image-stock/AAPL.png",
                    "ipoDate": "1980-12-12",
                    "defaultImage": False,
                    "isEtf": False,
                    "isActivelyTrading": True,
                    "isAdr": False,
                    "isFund": False
            },
    }

class StocksResponse(BaseModel):
    """Basic stock information response"""
    symbol: str = Field(..., description="Stock ticker symbol")
    companyName: str = Field(..., description="Company name")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "6898.HK",
                "companyName": "China Aluminum Cans Holdings Limited"
            }
        }

class FinancialStatementSymbolResponse(BaseModel):
    """Financial statement symbol response"""
    symbol: str = Field(..., description="Stock ticker symbol")
    companyName: str = Field(..., description="Company name")
    tradingCurrency: str = Field(..., description="Trading currency")
    reportingCurrency: str = Field(..., description="Reporting currency")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "tradingCurrency": "USD",
                "reportingCurrency": "USD"
            }
        }
   


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


class CIKResponse(BaseModel):
    """CIK (Central Index Key) response"""
    cik: str = Field(..., description="Central Index Key")
    companyName: str = Field(..., description="Company name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cik": "0002036063",
                "companyName": "LUZ Capital Partners, LLC"
            }
        }


class SymbolChangeResponse(BaseModel):
    """Stock symbol change information"""
    date: str = Field(..., description="Date of symbol change")
    companyName: str = Field(..., description="Company name")
    oldSymbol: str = Field(..., description="Previous ticker symbol")
    newSymbol: str = Field(..., description="New ticker symbol")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-02-03",
                "companyName": "XPLR Infrastructure, LP",
                "oldSymbol": "NEP",
                "newSymbol": "XIFR"
            }
        }


class ETFListResponse(BaseModel):
    """ETF symbol and name"""
    symbol: str = Field(..., description="ETF ticker symbol")
    name: str = Field(..., description="ETF name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "GULF",
                "name": "WisdomTree Middle East Dividend Fund"
            }
        }


class ExchangeResponse(BaseModel):
    """Stock exchange information"""
    exchange: str = Field(..., description="Exchange code")
    name: str = Field(..., description="Exchange name")
    countryName: str = Field(..., description="Country name")
    countryCode: str = Field(..., description="Country code")
    symbolSuffix: str = Field(..., description="Symbol suffix")
    delay: str = Field(..., description="Data delay information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "exchange": "AMEX",
                "name": "New York Stock Exchange Arca",
                "countryName": "United States of America",
                "countryCode": "US",
                "symbolSuffix": "N/A",
                "delay": "Real-time"
            }
        }


class SectorResponse(BaseModel):
    """Industry sector"""
    sector: str = Field(..., description="Sector name")
    
    class Config:
        json_schema_extra = {
            "example": {"sector": "Basic Materials"}
        }


class IndustryResponse(BaseModel):
    """Industry classification"""
    industry: str = Field(..., description="Industry name")
    
    class Config:
        json_schema_extra = {
            "example": {"industry": "Steel"}
        }


class CountryResponse(BaseModel):
    """Country code"""
    country: str = Field(..., description="Country code")
    
    class Config:
        json_schema_extra = {
            "example": {"country": "US"}
        }


class CompanyProfileResponse(BaseModel):
    """Detailed company profile information"""
    symbol: str = Field(..., description="Stock ticker symbol")
    price: float = Field(..., description="Current stock price")
    marketCap: float = Field(..., description="Market capitalization")
    beta: Optional[float] = Field(None, description="Beta coefficient")
    lastDividend: Optional[float] = Field(None, description="Last dividend")
    range: str = Field(..., description="52-week price range")
    change: float = Field(..., description="Price change")
    changePercentage: float = Field(..., description="Price change percentage")
    volume: int = Field(..., description="Trading volume")
    averageVolume: int = Field(..., description="Average volume")
    companyName: str = Field(..., description="Company name")
    currency: str = Field(..., description="Currency")
    cik: str = Field(..., description="CIK number")
    isin: str = Field(..., description="ISIN")
    cusip: str = Field(..., description="CUSIP")
    exchangeFullName: str = Field(..., description="Full exchange name")
    exchange: str = Field(..., description="Exchange code")
    industry: str = Field(..., description="Industry")
    website: str = Field(..., description="Company website")
    description: str = Field(..., description="Company description")
    ceo: str = Field(..., description="CEO name")
    sector: str = Field(..., description="Sector")
    country: str = Field(..., description="Country code")
    fullTimeEmployees: str = Field(..., description="Number of employees")
    phone: str = Field(..., description="Phone number")
    address: str = Field(..., description="Address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    zip: str = Field(..., description="Zip code")
    image: str = Field(..., description="Company logo URL")
    ipoDate: str = Field(..., description="IPO date")
    defaultImage: bool = Field(..., description="Is default image")
    isEtf: bool = Field(..., description="Is ETF")
    isActivelyTrading: bool = Field(..., description="Is actively trading")
    isAdr: bool = Field(..., description="Is ADR")
    isFund: bool = Field(..., description="Is fund")
    
    class Config:
        extra = "allow"


class CompanyNotesResponse(BaseModel):
    """Company notes information"""
    cik: str = Field(..., description="CIK number")
    symbol: str = Field(..., description="Stock symbol")
    title: str = Field(..., description="Note title")
    exchange: str = Field(..., description="Exchange")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cik": "0000320193",
                "symbol": "AAPL",
                "title": "1.000% Notes due 2022",
                "exchange": "NASDAQ"
            }
        }


class DelistedCompanyResponse(BaseModel):
    """Delisted company information"""
    symbol: str = Field(..., description="Stock symbol")
    companyName: str = Field(..., description="Company name")
    exchange: str = Field(..., description="Exchange")
    ipoDate: str = Field(..., description="IPO date")
    delistedDate: str = Field(..., description="Delisted date")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BRQSF",
                "companyName": "Borqs Technologies, Inc.",
                "exchange": "PNK",
                "ipoDate": "2017-08-24",
                "delistedDate": "2025-02-03"
            }
        }


class EmployeeCountResponse(BaseModel):
    """Employee count information"""
    symbol: str = Field(..., description="Stock symbol")
    cik: str = Field(..., description="CIK number")
    acceptanceTime: str = Field(..., description="Acceptance time")
    periodOfReport: str = Field(..., description="Period of report")
    companyName: str = Field(..., description="Company name")
    formType: str = Field(..., description="Form type")
    filingDate: str = Field(..., description="Filing date")
    employeeCount: int = Field(..., description="Employee count")
    source: str = Field(..., description="Source URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "cik": "0000320193",
                "acceptanceTime": "2024-11-01 06:01:36",
                "periodOfReport": "2024-09-28",
                "companyName": "Apple Inc.",
                "formType": "10-K",
                "filingDate": "2024-11-01",
                "employeeCount": 164000,
                "source": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index.htm"
            }
        }


class MarketCapResponse(BaseModel):
    """Market capitalization data"""
    symbol: str = Field(..., description="Stock symbol")
    date: str = Field(..., description="Date")
    marketCap: float = Field(..., description="Market capitalization")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "date": "2025-02-04",
                "marketCap": 3500823120000
            }
        }


class SharesFloatResponse(BaseModel):
    """Shares float and liquidity data"""
    symbol: str = Field(..., description="Stock symbol")
    date: str = Field(..., description="Date and time")
    freeFloat: float = Field(..., description="Free float percentage")
    floatShares: float = Field(..., description="Float shares")
    outstandingShares: float = Field(..., description="Outstanding shares")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "date": "2025-02-04 17:01:35",
                "freeFloat": 99.9095,
                "floatShares": 15024290700,
                "outstandingShares": 15037900000
            }
        }


class MergerAcquisitionResponse(BaseModel):
    """Merger and acquisition information"""
    symbol: str = Field(..., description="Acquiring company symbol")
    companyName: str = Field(..., description="Acquiring company name")
    cik: str = Field(..., description="Acquiring company CIK")
    targetedCompanyName: str = Field(..., description="Target company name")
    targetedCik: str = Field(..., description="Target company CIK")
    targetedSymbol: str = Field(..., description="Target company symbol")
    transactionDate: str = Field(..., description="Transaction date")
    acceptedDate: str = Field(..., description="Accepted date")
    link: str = Field(..., description="Filing link")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "NLOK",
                "companyName": "NortonLifeLock Inc.",
                "cik": "0000849399",
                "targetedCompanyName": "MoneyLion Inc.",
                "targetedCik": "0001807846",
                "targetedSymbol": "ML",
                "transactionDate": "2025-02-03",
                "acceptedDate": "2025-02-03 06:01:10",
                "link": "https://www.sec.gov/Archives/edgar/data/849399/000114036125002752/ny20039778x6_s4.htm"
            }
        }


class ExecutiveResponse(BaseModel):
    """Company executive information"""
    title: str = Field(..., description="Executive title")
    name: str = Field(..., description="Executive name")
    pay: Optional[float] = Field(None, description="Compensation")
    currencyPay: str = Field(..., description="Currency")
    gender: Optional[str] = Field(None, description="Gender")
    yearBorn: Optional[int] = Field(None, description="Year born")
    active: Optional[bool] = Field(None, description="Is active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Vice President of Worldwide Sales",
                "name": "Mr. Michael Fenger",
                "pay": None,
                "currencyPay": "USD",
                "gender": "male",
                "yearBorn": None,
                "active": None
            }
        }


class ExecutiveCompensationResponse(BaseModel):
    """Executive compensation details"""
    cik: str = Field(..., description="CIK number")
    symbol: str = Field(..., description="Stock symbol")
    companyName: str = Field(..., description="Company name")
    filingDate: str = Field(..., description="Filing date")
    acceptedDate: str = Field(..., description="Accepted date")
    nameAndPosition: str = Field(..., description="Executive name and position")
    year: int = Field(..., description="Compensation year")
    salary: float = Field(..., description="Base salary")
    bonus: float = Field(..., description="Bonus")
    stockAward: float = Field(..., description="Stock award")
    optionAward: float = Field(..., description="Option award")
    incentivePlanCompensation: float = Field(..., description="Incentive plan compensation")
    allOtherCompensation: float = Field(..., description="Other compensation")
    total: float = Field(..., description="Total compensation")
    link: str = Field(..., description="Filing link")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cik": "0000320193",
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "filingDate": "2025-01-10",
                "acceptedDate": "2025-01-10 16:31:18",
                "nameAndPosition": "Kate Adams Senior Vice President",
                "year": 2023,
                "salary": 1000000,
                "bonus": 0,
                "stockAward": 22323641,
                "optionAward": 0,
                "incentivePlanCompensation": 3571150,
                "allOtherCompensation": 46914,
                "total": 26941705,
                "link": "https://www.sec.gov/Archives/edgar/data/320193/000130817925000008/0001308179-25-000008-index.htm"
            }
        }

class PriceCandle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class SupportResistanceLevel(BaseModel):
    price: float
    strength: int = 1  # 1=weak, 3=strong (จำนวนครั้งที่ราคามาชนแล้วเด้ง)
    type: str  # "SUPPORT" or "RESISTANCE"

class TechnicalAnalysisResult(BaseModel):
    symbol: str
    current_price: float
    trend: str = Field(..., description="UPTREND, DOWNTREND, SIDEWAY")
    rsi: float
    signal: str = Field(..., description="BUY_DIP, SELL_RALLY, WAIT")
    support_levels: List[float]
    resistance_levels: List[float]
    analyzed_at: datetime = Field(default_factory=datetime.now)

class TradeRecord(BaseModel):
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    pnl_percent: float
    win: bool

class BacktestResult(BaseModel):
    symbol: str
    strategy_name: str = Field(default="buy_the_dip", description="Name of the strategy used")
    strategy_config: dict = Field(default_factory=dict, description="Strategy configuration used")
    period_days: int
    total_trades: int
    win_rate: float = Field(..., description="Percentage of winning trades")
    avg_return: float = Field(..., description="Average return per trade (%)")
    best_trade: float = Field(..., description="Best trade return (%)")
    worst_trade: float = Field(..., description="Worst trade return (%)")
    total_return: float = Field(default=0.0, description="Total cumulative return (%)")
    sharpe_ratio: float = Field(default=0.0, description="Risk-adjusted return metric")
    max_drawdown: float = Field(default=0.0, description="Maximum drawdown (%)")
    profit_factor: float = Field(default=0.0, description="Ratio of gross profit to gross loss")
    recent_trades: List[TradeRecord] = Field(default_factory=list, description="Recent trade records")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "strategy_name": "buy_the_dip",
                "strategy_config": {
                    "name": "buy_the_dip",
                    "holding_days": 5,
                    "stop_loss_pct": 5.0,
                    "take_profit_pct": 10.0,
                    "parameters": {
                        "ema_length": 200,
                        "rsi_threshold": 35
                    }
                },
                "period_days": 365,
                "total_trades": 24,
                "win_rate": 62.5,
                "avg_return": 2.34,
                "best_trade": 12.5,
                "worst_trade": -4.2,
                "total_return": 56.16,
                "sharpe_ratio": 1.45,
                "max_drawdown": 8.3,
                "profit_factor": 2.1,
                "recent_trades": []
            }
        }