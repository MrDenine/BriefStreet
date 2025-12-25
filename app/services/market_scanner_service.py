import asyncio
from typing import List, Optional
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.models.market_data import TechnicalAnalysisResult

class MarketScannerService:
    def __init__(self, analysis_service: TechnicalAnalysisService):
        self.analysis_service = analysis_service

    async def scan(self, symbols: List[str], filter_signal: Optional[str] = None) -> List[TechnicalAnalysisResult]:
        """
        Scan multiple symbols and filter results.
        :param symbols: List of symbols to scan (e.g., ["BTC-USD", "ETH-USD"])
        :param filter_signal: If provided, return only results with this signal (e.g., "BUY_DIP")
        """
        results = []
        
        # --- Technique: Concurrency Control ---
        # เราจะแบ่งยิงทีละ 5-10 requests (Semaphore)
        sem = asyncio.Semaphore(10) 

        async def analyze_safe(symbol):
            async with sem:
                try:
                    # เรียกใช้ Logic วิเคราะห์ที่เราทำไว้แล้ว
                    return await self.analysis_service.analyze(symbol)
                except Exception as e:
                    # ถ้าตัวไหน Error (เช่นไม่มีข้อมูล) ให้ข้ามไป
                    print(f"Skipping {symbol}: {e}")
                    return None

        # สร้าง Task สำหรับทุก Symbol
        tasks = [analyze_safe(sym) for sym in symbols]
        
        all_results = await asyncio.gather(*tasks)

        for res in all_results:
            if res:
                if filter_signal is None or res.signal == filter_signal:
                    results.append(res)
        
        return results