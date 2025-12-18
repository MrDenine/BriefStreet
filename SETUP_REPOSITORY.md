# 🎯 Setup Guide - Multi-Database Repository Pattern

## 📋 สรุปการเปลี่ยนแปลง

เพิ่ม **Repository Pattern** พร้อมรองรับ PostgreSQL และ Multi-Environment Configuration

### ไฟล์ที่สร้างใหม่:

```
app/
├── repositories/
│   ├── __init__.py
│   ├── base.py                              # Interface definitions
│   ├── cache/
│   │   └── sql_cache.py                     # SQLite/Postgres cache implementation
│   └── market_data/
│       └── sql_market_data.py               # SQLite/Postgres market data implementation
├── models/
│   └── market_data_storage.py               # Models สำหรับเก็บ market data
├── services/
│   └── market_data_storage.py               # Service layer
├── config/
│   └── repository_config.py                 # Environment-specific DB config
└── core/
    └── dependencies.py                      # Repository factory (DI)
```

### ไฟล์ที่แก้ไข:

- `app/core/config.py` - เพิ่ม ENVIRONMENT และ PostgreSQL config
- `app/core/database.py` - รองรับทั้ง SQLite และ PostgreSQL
- `app/main.py` - แสดง environment info ตอน startup
- `app/api/v1/endpoints/analyze.py` - ใช้ repository แทน direct DB access
- `requirements.txt` - เพิ่ม `asyncpg` สำหรับ PostgreSQL

---

## 🚀 การติดตั้ง

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

**สิ่งที่เพิ่มมา:**
- `asyncpg` - PostgreSQL async driver

### 2. Setup Environment Files

**Development (SQLite):**
```powershell
# ใช้ไฟล์ .env.development
cp .env.development .env

# หรือกำหนดใน .env:
ENVIRONMENT=development
```

**UAT (PostgreSQL):**
```powershell
# ใช้ไฟล์ .env.uat
cp .env.uat .env

# กำหนด PostgreSQL connection:
ENVIRONMENT=uat
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=briefstreet
```

### 3. Setup PostgreSQL (สำหรับ UAT)

```powershell
# สร้าง database
psql -U postgres
CREATE DATABASE briefstreet_uat;
\q
```

---

## 📊 Database Configuration ตาม Environment

| Environment | Cache DB | Market Data DB | Strategy |
|-------------|----------|----------------|----------|
| **Development** | SQLite | SQLite | PRIMARY |
| **UAT** | PostgreSQL | PostgreSQL | PRIMARY |
| **Production** | PostgreSQL | PostgreSQL | PRIMARY |

---

## 🎮 การใช้งาน

### รัน Development (SQLite)
```powershell
$env:ENVIRONMENT="development"
uvicorn app.main:app --reload
```

**Output:**
```
🚀 Starting BriefStreet...
🌍 Environment: development
📊 Database Configuration:
  - cache: primary (Primary: sqlite)
  - market_data: primary (Primary: sqlite)
✅ Database connected successfully
```

### รัน UAT (PostgreSQL)
```powershell
$env:ENVIRONMENT="uat"
uvicorn app.main:app --reload
```

**Output:**
```
🚀 Starting BriefStreet...
🌍 Environment: uat
📊 Database Configuration:
  - cache: primary (Primary: postgres)
  - market_data: primary (Primary: postgres)
✅ Database connected successfully
```

---

## 🔧 ตัวอย่างการใช้งาน Repository

### ใน Endpoint (analyze.py):

```python
from app.core.dependencies import get_cache_repository
from app.repositories.base import ICacheRepository

@router.post("/analyze/{symbol}")
async def analyze_earnings(
    symbol: str, 
    cache_repo: ICacheRepository = Depends(get_cache_repository)  # 🎯
):
    # ใช้ repository - ไม่สนว่าข้างหลังเป็น DB อะไร!
    cached = await cache_repo.get(symbol, date)
    
    if not cached:
        # วิเคราะห์ใหม่
        result = analyze(...)
        await cache_repo.save(symbol, date, result)
    
    return result
```

### Market Data Storage Service:

```python
from app.services.market_data_storage import MarketDataStorageService

# สร้าง service
service = MarketDataStorageService(market_data_repo)

# บันทึก transcript
await service.store_transcript(
    symbol="AAPL",
    quarter_date="2024-10-25",
    content="Earnings call transcript...",
    metadata={"source": "FMP"}
)

# ดึง transcript
transcript = await service.get_transcript("AAPL", "2024-10-25")
```

---

## 📁 โครงสร้าง Database

### Tables ที่ถูกสร้าง:

1. **earnings_cache** (เดิม)
   - id, symbol, quarter_date, analysis_json, created_at

2. **transcripts** (ใหม่)
   - id, symbol, quarter_date, content, metadata, created_at, updated_at

3. **financial_data** (ใหม่)
   - id, symbol, year, quarter, data_type, data, source, created_at, updated_at

---

## 🎯 ข้อดีของ Architecture นี้

✅ **Flexibility** - เปลี่ยน DB ได้โดยแก้แค่ config  
✅ **Testability** - Mock repository ง่าย  
✅ **Maintainability** - แยก business logic กับ data access  
✅ **Scalability** - เพิ่ม DB/domain ใหม่ได้ง่าย  
✅ **Environment-aware** - Dev/UAT/Prod ใช้ DB ต่างกัน  

---

## 🧪 Testing

```powershell
# Test กับ SQLite (development)
$env:ENVIRONMENT="development"
pytest

# Test กับ PostgreSQL (uat) 
$env:ENVIRONMENT="uat"
pytest
```

---

## 📝 Next Steps

1. ✅ เพิ่ม Postgres support
2. ✅ Repository Pattern implementation
3. ✅ Environment configuration
4. 🔄 เพิ่ม Firebase support (optional)
5. 🔄 เพิ่ม Dual-Write strategy (optional)
6. 🔄 Migration tools (Alembic)
