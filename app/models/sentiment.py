# app/models/sentiment.py
from pydantic import BaseModel, Field
from typing import List

class KeyHighlight(BaseModel):
    topic: str = Field(description="หัวข้อประเด็นสำคัญ เช่น Revenue, Guidance, New Product")
    summary: str = Field(description="สรุปเนื้อหาแบบสั้น กระชับ")
    sentiment: str = Field(description="อารมณ์ของข่าวนั้น: Positive, Negative, หรือ Neutral")

class AnalysisResponse(BaseModel):
    symbol: str
    overall_sentiment_score: int = Field(description="คะแนนรวม 0-100 (0=แย่มาก, 100=ดีมาก)")
    ceo_tone: str = Field(description="น้ำเสียงผู้บริหาร เช่น Confident, Cautious, Optimistic")
    highlights: List[KeyHighlight]