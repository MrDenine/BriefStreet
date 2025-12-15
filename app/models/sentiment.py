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

class ChatRequest(BaseModel):
    question: str = Field(description="คำถามที่ User อยากรู้เกี่ยวกับหุ้นตัวนี้")

class ChatResponse(BaseModel):
    answer: str = Field(description="คำตอบจาก AI")

class SectionAnalysis(BaseModel):
    score: int = Field(description="คะแนนความมั่นใจ 0-100 ของช่วงนี้")
    tone: str = Field(description="น้ำเสียงหลัก เช่น Confident, Defensive, Evasive")
    key_point: str = Field(description="ประเด็นสำคัญที่สุดในช่วงนี้")

class ConsistencyResponse(BaseModel):
    symbol: str
    prepared_remarks: SectionAnalysis = Field(description="วิเคราะห์ช่วงผู้บริหารพูดเปิด (Scripted)")
    qa_session: SectionAnalysis = Field(description="วิเคราะห์ช่วงถาม-ตอบ (Unscripted)")
    consistency_score: int = Field(description="คะแนนความคงเส้นคงวา (100=พูดตรงกัน, 0=หน้ามือเป็นหลังมือ)")
    red_flag_warning: str = Field(description="คำเตือนถ้าพฤติกรรมน่าสงสัย (เช่น ช่วง Q&A คะแนนร่วงหนัก)")