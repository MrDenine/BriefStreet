import httpx
from app.core.config import settings

async def get_mock_transcript(symbol: str):
    return [
        {
            "date": "2024-10-25",
            "content": f"""
                    Operator: Good afternoon. Welcome to the {symbol} Q4 Earnings Call.
                    CEO: Thank you. We are happy to report a record-breaking quarter. 
                    Revenue is up 25% year-over-year due to strong demand in our AI sector.
                    However, we are seeing some supply chain headwinds in Asia, which might affect Q1 margins slightly.
                    Overall, we are very confident in our long-term strategy.
                    """
        }
    ]

async def get_earnings_transcript(symbol: str):
    """
    ดึง Transcript จริงจาก Financial Modeling Prep (FMP)
    """
    if not settings.FMP_API_KEY or settings.FMP_API_KEY == "xxxxxxxx":
        print("⚠️ ไม่พบ FMP API Key -> ใช้ Mock Data แทน")
        return await get_mock_transcript(symbol)

    url = f"https://financialmodelingprep.com/api/v3/earning_call_transcript/{symbol}?quarter=3&year=2024&apikey={settings.FMP_API_KEY}" 
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            data = response.json()
            
            if not data:
                print(f"❌ ไม่พบข้อมูล Transcript ของ {symbol} -> ใช้ Mock แทน")
                return await get_mock_transcript(symbol)
                
            return {
                "date": data[0]['date'], 
                "content": data[0]['content']
            }
            
        except Exception as e:
            print(f"🔥 Error fetching data: {e}")
            return await get_mock_transcript(symbol)