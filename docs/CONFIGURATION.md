# Configuration Guide - BriefStreet API

## 📋 ภาพรวม

BriefStreet API ใช้ **environment variables** และ **`.env` file** สำหรับการกำหนดค่า ทำให้สามารถปรับแต่งพฤติกรรมของระบบได้โดยไม่ต้องแก้โค้ด

---

## 🔧 การตั้งค่า

### 1. สร้างไฟล์ `.env`

```bash
cp .env.example .env
```

### 2. กำหนดค่าที่จำเป็น

แก้ไข `.env` และใส่ค่าที่ต้องการ:

```env
# ✅ REQUIRED
OPENAI_API_KEY=sk-your-openai-key-here
FMP_API_KEY=your-fmp-key-here

# ⚙️ OPTIONAL (มี default อยู่แล้ว)
DATA_PROVIDER=fmp
LLM_MODEL=gpt-4o-mini
```

---

## 📚 รายการ Configuration ทั้งหมด

### 🔑 **API Keys** (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key สำหรับ LLM | `sk-proj-...` |
| `FMP_API_KEY` | Financial Modeling Prep API key | `abc123...` |

---

### 🎯 **Data Provider**

| Variable | Options | Default | Description |
|----------|---------|---------|-------------|
| `DATA_PROVIDER` | `fmp`, `yfinance`, `mock` | `fmp` | เลือก data source |

**การใช้งาน:**
- `fmp` - Production (ต้องใช้ API key)
- `yfinance` - Development (ฟรี, ไม่มี transcript)
- `mock` - Testing (ข้อมูล fake)

---

### 🤖 **LLM Configuration**

#### Model Selection

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODEL` | `gpt-4o-mini` | Model สำหรับวิเคราะห์ transcript |
| `LLM_CHAT_MODEL` | `gpt-4o-mini` | Model สำหรับ chat |
| `LLM_CONSISTENCY_MODEL` | `gpt-4o-mini` | Model สำหรับ consistency analysis |

**ตัวเลือก:** `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`

#### Text Limits (Characters)

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `LLM_TRANSCRIPT_MAX_LENGTH_ANALYSIS` | `15000` | ความยาว transcript สำหรับ analysis |
| `LLM_TRANSCRIPT_MAX_LENGTH_CHAT` | `25000` | ความยาว transcript สำหรับ chat |
| `LLM_TRANSCRIPT_MAX_LENGTH_CONSISTENCY_PREPARED` | `10000` | Prepared remarks |
| `LLM_TRANSCRIPT_MAX_LENGTH_CONSISTENCY_QA` | `10000` | Q&A session |

**Tips:** ลดค่านี้เพื่อประหยัด token costs

#### Retry Configuration

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `LLM_MAX_RETRIES` | `2` | จำนวนครั้งที่ retry เมื่อ API error |
| `LLM_RETRY_DELAY` | `2.0` | หน่วง (วินาที) ก่อน retry |

#### Messages & Prompts

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `LLM_DEFAULT_NOT_FOUND_MESSAGE` | `ข้อมูลนี้ไม่ได้...` | ข้อความเมื่อไม่เจอคำตอบ |
| `LLM_SYSTEM_PROMPT_ANALYSIS` | `You are a helpful...` | System prompt สำหรับ analysis |
| `LLM_SYSTEM_PROMPT_CHAT` | `You are a helpful...` | System prompt สำหรับ chat |
| `LLM_SYSTEM_PROMPT_CONSISTENCY` | `You are a cynical...` | System prompt สำหรับ consistency |

---

### 💰 **Valuation Configuration**

#### DCF Parameters

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `VALUATION_DCF_GROWTH_RATE` | `0.05` | อัตราการเติบโต (5%) |
| `VALUATION_DCF_DISCOUNT_RATE` | `0.10` | Discount rate / WACC (10%) |
| `VALUATION_DCF_TERMINAL_GROWTH` | `0.02` | Terminal growth (2%) |
| `VALUATION_DCF_PROJECTION_YEARS` | `5` | จำนวนปีที่ project |

#### Graham Number

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `VALUATION_GRAHAM_MULTIPLIER` | `22.5` | Benjamin Graham's multiplier |

#### Peer Comparison Defaults

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `VALUATION_DEFAULT_PEER_PE` | `25.0` | Default P/E เมื่อไม่มีข้อมูล peer |
| `VALUATION_DEFAULT_SECTOR_PBV` | `4.5` | Default P/BV ของ sector |

---

### 🌐 **FMP Provider Settings**

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `FMP_BASE_URL` | `https://financialmodelingprep.com/stable` | FMP API endpoint |
| `FMP_TIMEOUT` | `30.0` | Request timeout (วินาที) |
| `FMP_MAX_RETRIES` | `3` | จำนวนครั้งที่ retry |
| `FMP_RETRY_DELAY` | `1.0` | หน่วงก่อน retry (วินาที) |
| `FMP_RATE_LIMIT_RETRY_AFTER` | `60` | รอเมื่อโดน rate limit (วินาที) |

---

### 📊 **YFinance Provider Settings**

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `YFINANCE_TIMEOUT` | `30.0` | Request timeout (วินาที) |

---

### 🔢 **Default Query Parameters**

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `DEFAULT_QUARTER` | `3` | Q3 |
| `DEFAULT_YEAR` | `2024` | ปีปัจจุบัน |
| `DEFAULT_FINANCIAL_HISTORY_LIMIT` | `5` | จำนวนปีย้อนหลัง |
| `DEFAULT_PEERS_LIMIT` | `5` | จำนวน peer companies |

---

### 💾 **Cache Configuration**

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `CACHE_ENABLED` | `true` | เปิด/ปิด caching |
| `CACHE_TTL` | `86400` | Cache lifetime (24 ชม. = 86400 วินาที) |

---

### 🎛️ **Feature Flags**

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `ENABLE_CONSISTENCY_ANALYSIS` | `true` | เปิด/ปิด consistency analysis endpoint |
| `ENABLE_VALUATION` | `true` | เปิด/ปิด valuation feature |

---

### 📝 **Logging**

| Variable | Default | Options |
|----------|---------|---------|
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_MAX_QUESTION_LENGTH` | `100` | จำนวน chars สูงสุดใน log |

---

## 🎨 Use Cases

### 1. **Production Setup**

```env
DATA_PROVIDER=fmp
LLM_MODEL=gpt-4o-mini
FMP_MAX_RETRIES=5
CACHE_ENABLED=true
LOG_LEVEL=WARNING
```

### 2. **Development Setup**

```env
DATA_PROVIDER=yfinance  # ฟรี!
LLM_MODEL=gpt-4o-mini
LLM_MAX_RETRIES=1
CACHE_ENABLED=false
LOG_LEVEL=DEBUG
```

### 3. **Testing Setup**

```env
DATA_PROVIDER=mock  # ไม่มี API calls
LLM_MODEL=gpt-4o-mini
CACHE_ENABLED=false
LOG_LEVEL=DEBUG
```

### 4. **Cost Optimization**

```env
# ลด token usage
LLM_TRANSCRIPT_MAX_LENGTH_ANALYSIS=10000
LLM_TRANSCRIPT_MAX_LENGTH_CHAT=15000

# ลด API calls
FMP_MAX_RETRIES=2
LLM_MAX_RETRIES=1

# เพิ่ม cache
CACHE_ENABLED=true
CACHE_TTL=604800  # 7 วัน
```

### 5. **High Accuracy Setup**

```env
# ใช้ model ที่ดีกว่า
LLM_MODEL=gpt-4o
LLM_CHAT_MODEL=gpt-4o

# ให้ context เยอะขึ้น
LLM_TRANSCRIPT_MAX_LENGTH_ANALYSIS=30000
LLM_TRANSCRIPT_MAX_LENGTH_CHAT=40000

# Valuation ละเอียดขึ้น
VALUATION_DCF_PROJECTION_YEARS=10
```

---

## 🔄 การเปลี่ยนค่าแบบ Runtime

บางค่าสามารถเปลี่ยนได้ขณะรันโปรแกรม:

```python
from app.services import market_data
from app.data_sources import MockProvider

# เปลี่ยน provider
market_data.set_provider(MockProvider())

# ใช้ต่อได้เลย
result = await market_data.get_earnings_transcript("AAPL", 3, 2024)
```

---

## ⚠️ ข้อควรระวัง

1. **ห้าม commit `.env`** - มี API keys ลับ
2. **ใช้ `.env.example`** - สำหรับ template
3. **LLM costs** - ระวัง `MAX_LENGTH` ที่สูงเกินไป
4. **FMP rate limit** - Free tier มี limit 250 requests/day

---

## 📖 สรุป

- ✅ ค่า default ครอบคลุมทุก use case
- ✅ Override เฉพาะที่ต้องการใน `.env`
- ✅ ใช้ `.env.example` เป็น template
- ✅ ปรับค่าตาม environment (dev/staging/prod)

---

**เอกสารเพิ่มเติม:** [DATA_SOURCES.md](DATA_SOURCES.md)
