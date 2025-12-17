# BriefStreet - Multi-Provider Data Source Architecture

## 📁 โครงสร้างโปรเจค

```
app/
├── data_sources/          # ✨ NEW: Data provider abstraction layer
│   ├── __init__.py
│   ├── base.py           # Abstract base class
│   ├── fmp_provider.py   # Financial Modeling Prep
│   ├── yfinance_provider.py  # Yahoo Finance (free)
│   └── mock_provider.py  # Mock data for testing
├── services/
│   ├── market_data.py    # High-level facade (refactored)
│   ├── llm_service.py
│   └── valuation_service.py
└── core/
    ├── exceptions.py     # ✨ Updated with provider exceptions
    └── config.py         # ✨ Updated with DATA_PROVIDER setting
```

## 🎯 Provider Architecture

### การออกแบบ

ใช้ **Strategy Pattern** และ **Dependency Injection** เพื่อ:
- แยก business logic ออกจาก data source implementation
- รองรับหลาย providers พร้อม fallback mechanism
- ทดสอบได้ง่ายด้วย mock provider
- เพิ่ม provider ใหม่โดยไม่แก้โค้ดเดิม

### Providers ที่รองรับ

| Provider | Features | Cost | Use Case |
|----------|----------|------|----------|
| **FMP** (Default) | Transcripts, Metrics, Peers | Paid API | Production |
| **YFinance** | Metrics only | Free | Development/Fallback |
| **Mock** | All (fake data) | Free | Testing/Demo |

## ⚙️ การตั้งค่า

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 2. กำหนด Provider ใน `.env`

```env
# ตัวเลือก: fmp, yfinance, mock
DATA_PROVIDER=fmp

# API Keys
FMP_API_KEY=your_fmp_key_here
OPENAI_API_KEY=your_openai_key_here

# Optional: Override default settings
FMP_TIMEOUT=30.0
FMP_MAX_RETRIES=3
DEFAULT_PEERS_LIMIT=5
```

**ดูตัวอย่างครบใน `.env.example`**

### 3. เปลี่ยน Provider แบบ Runtime

```python
from app.services import market_data
from app.data_sources import YFinanceProvider, MockProvider

# เปลี่ยนเป็น YFinance
market_data.set_provider(YFinanceProvider())

# หรือใช้ Mock สำหรับ testing
market_data.set_provider(MockProvider())

# Reset กลับค่า default
market_data.reset_provider()
```

## 🔧 การใช้งาน

### Basic Usage (Single Provider)

```python
from app.services import market_data

# ใช้ provider ที่กำหนดใน config
transcript = await market_data.get_earnings_transcript("AAPL", 3, 2024)
metrics = await market_data.get_financial_metrics("AAPL")
peers = await market_data.get_peers_valuation("AAPL")
```

### Fallback Mode (Multi-Provider)

```python
# ถ้า provider หลักล้มเหลว จะลองอันอื่นอัตโนมัติ
transcript = await market_data.get_earnings_transcript(
    "AAPL", 3, 2024, 
    fallback=True  # ✨ เปิดใช้ fallback
)

metrics = await market_data.get_financial_metrics(
    "AAPL",
    fallback=True  # FMP → YFinance → Mock
)
```

## 🧪 Testing

### ใช้ Mock Provider ใน Unit Tests

```python
import pytest
from app.services import market_data
from app.data_sources import MockProvider

@pytest.fixture(autouse=True)
def setup_mock_provider():
    """ใช้ Mock provider สำหรับทุก test"""
    market_data.set_provider(MockProvider())
    yield
    market_data.reset_provider()

async def test_get_transcript():
    # ไม่มี API call จริง, ไม่มีค่าใช้จ่าย
    result = await market_data.get_earnings_transcript("AAPL", 3, 2024)
    assert result["date"] is not None
    assert "content" in result
```

## 🆕 Exception Types

### Provider-Specific Exceptions

```python
from app.core.exceptions import (
    ProviderNotImplementedException,    # Feature not supported
    ProviderUnavailableException,       # Provider temporarily down
    AllProvidersFailedException         # All fallbacks failed
)

# ตัวอย่างการ handle
try:
    transcript = await market_data.get_earnings_transcript("AAPL", 3, 2024)
except ProviderNotImplementedException as e:
    # YFinance ไม่รองรับ transcripts
    print(f"{e.details['provider']} doesn't support {e.details['feature']}")
except AllProvidersFailedException as e:
    # ทุก provider ล้มเหลว
    print(f"Attempted: {e.details['attempted_providers']}")
    print(f"Errors: {e.details['errors']}")
```

## 📝 เพิ่ม Provider ใหม่

### ขั้นตอน:

1. **สร้างไฟล์ใน `app/data_sources/`**

```python
# app/data_sources/alpha_vantage_provider.py
from app.data_sources.base import DataSourceProvider

class AlphaVantageProvider(DataSourceProvider):
    @property
    def name(self) -> str:
        return "AlphaVantage"
    
    async def get_transcript(self, symbol: str, quarter: int, year: int) -> Dict:
        # Implement...
        pass
    
    async def get_financial_metrics(self, symbol: str, limit: int = 5) -> Dict:
        # Implement...
        pass
    
    async def get_peers(self, symbol: str) -> List[str]:
        # Implement...
        pass
```

2. **เพิ่มใน `__init__.py`**

```python
from .alpha_vantage_provider import AlphaVantageProvider

__all__ = [
    "DataSourceProvider",
    "FMPProvider",
    "YFinanceProvider",
    "MockProvider",
    "AlphaVantageProvider",  # ✨ เพิ่มตรงนี้
]
```

3. **อัพเดท `market_data.py` (ถ้าต้องการ)**

```python
def get_provider() -> DataSourceProvider:
    provider_name = settings.DATA_PROVIDER.lower()
    
    if provider_name == 'alphavantage':  # ✨ เพิ่มตรงนี้
        return AlphaVantageProvider()
    # ... existing code
```

## 🚀 Best Practices

### 1. Production: ใช้ FMP + Fallback
```python
# config
DATA_PROVIDER=fmp

# code
metrics = await market_data.get_financial_metrics(
    symbol, 
    fallback=True  # Auto fallback to free alternatives
)
```

### 2. Development: ใช้ Mock
```python
DATA_PROVIDER=mock  # No API costs
```

### 3. Testing: Inject Mock Provider
```python
market_data.set_provider(MockProvider())
```

### 4. Feature Check
```python
try:
    transcript = await provider.get_transcript(symbol, q, year)
except ProviderNotImplementedException:
    # Use different provider
    pass
```

## 📊 Provider Feature Matrix

| Feature | FMP | YFinance | Mock |
|---------|-----|----------|------|
| Earnings Transcripts | ✅ | ❌ | ✅ |
| Financial Metrics | ✅ | ✅ | ✅ |
| Peer Comparison | ✅ | ❌ | ✅ |
| Historical Cash Flow | ✅ | ✅ | ✅ |
| Rate Limiting | Yes (API) | No | No |
| Cost | Paid | Free | Free |

## 🔍 Logging

Provider operations มี logging แบบนี้:

```
[FMP] Fetching transcript for AAPL Q3 2024
✅ [FMP] Successfully fetched transcript for AAPL (Date: 2024-11-01)
[YFinance] Fetching financial metrics for MSFT
✅ [YFinance] Successfully fetched financial metrics for MSFT
⚠️ [Mock] Transcript feature not supported
```

## 📚 สรุป

### ข้อดี
- ✅ Flexible: เปลี่ยน provider ได้ง่าย
- ✅ Testable: ใช้ Mock provider ใน tests
- ✅ Resilient: Fallback mechanism
- ✅ Maintainable: แยก concerns ชัดเจน
- ✅ Cost-effective: ใช้ free providers ได้

### Use Cases
- **Production**: FMP with fallback
- **Development**: YFinance (free)
- **Testing**: Mock (no API calls)
- **Demo**: Mock (realistic fake data)

---

สร้างโดย BriefStreet Team 🚀
