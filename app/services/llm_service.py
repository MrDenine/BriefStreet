# app/services/llm_service.py
import json
from openai import OpenAI
from app.core.config import settings
from app.models.sentiment import AnalysisResponse

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def analyze_transcript(symbol: str, text: str) -> AnalysisResponse:
    print(f"🤖 AI กำลังวิเคราะห์หุ้น {symbol}...")
    
    prompt = f"""
    You are an expert financial analyst. 
    Analyze the following earnings call transcript for {symbol}.
    Extract key highlights, determine the overall sentiment score (0-100), 
    and identify the CEO's tone.
    
    Transcript:
    {text[:15000]}  # ตัด text เพื่อป้องกัน Token เกิน (เบื้องต้น)
    """

    # ใช้ client.beta.chat.completions.parse เพื่อบังคับ Output เป็น Pydantic Model ทันที
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",  # รุ่นประหยัดแต่ฉลาด
        messages=[
            {"role": "system", "content": "You are a helpful financial assistant. Respond in JSON format only."},
            {"role": "user", "content": prompt},
        ],
        response_format=AnalysisResponse, # หัวใจสำคัญ: ส่ง Model ไปให้ AI ดูเลย
    )

    # ดึงข้อมูลที่ AI ตอบกลับมา
    result = completion.choices[0].message.parsed
    return result