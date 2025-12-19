# Testing Guide

## การติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

## การรันเทส

### รันทั้งหมด
```bash
pytest
```

### รันแบบมี Coverage Report
```bash
pytest --cov=app --cov-report=html
```

### รันเทสเฉพาะไฟล์
```bash
pytest tests/test_api.py
```

### รันเทสเฉพาะ Function
```bash
pytest tests/test_api.py::test_read_root
```

### รันแบบ Verbose
```bash
pytest -v
```

### รันแบบแสดง Output
```bash
pytest -s
```

### รัน Marker เฉพาะ (เช่น unit tests)
```bash
pytest -m unit
```

### ดู Coverage Report
เปิดไฟล์ `htmlcov/index.html` ใน Browser

## โครงสร้างเทส

```
tests/
├── __init__.py
├── conftest.py          # Fixtures และ Configuration
├── test_api.py          # เทส API Endpoints
├── test_services.py     # เทส Business Logic
├── test_database.py     # เทส Database Operations
└── test_models.py       # เทส Pydantic Models
```

## ตัวอย่าง Fixtures

### `client` - Test Client พร้อม Database Override
```python
@pytest.mark.asyncio
async def test_example(client):
    response = await client.get("/")
    assert response.status_code == 200
```

### `test_session` - Database Session
```python
@pytest.mark.asyncio
async def test_db(test_session):
    # ทำงานกับ Database
    pass
```

### `mock_transcript` - Mock Data
```python
def test_example(mock_transcript):
    assert "content" in mock_transcript[0]
```

## Best Practices

1. **ใช้ Mock สำหรับ External Services** (OpenAI, FMP API)
2. **ใช้ In-Memory Database** สำหรับ Testing
3. **เทสทั้ง Success และ Error Cases**
4. **Test Coverage ควรอยู่ที่ 80%+**
5. **ใช้ Fixtures ให้เป็น** เพื่อลด Code Duplication

## Continuous Integration

Push code ไป GitHub จะรันเทสอัตโนมัติผ่าน GitHub Actions
