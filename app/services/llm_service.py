# app/services/llm_service.py
import json
from openai import OpenAI
from app.core.config import settings
from app.models.sentiment import AnalysisResponse , ConsistencyResponse

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

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",  
        messages=[
            {"role": "system", "content": "You are a helpful financial assistant. Respond in JSON format only."},
            {"role": "user", "content": prompt},
        ],
        response_format=AnalysisResponse, 
    )

    result = completion.choices[0].message.parsed
    return result

async def chat_with_transcript(symbol: str, text: str, question: str) -> str:
    print(f"💬 User กำลังถามเกี่ยวกับ {symbol}: {question}")
    
    prompt = f"""
    You are an expert financial analyst assistant. 
    The user is asking a question about the earnings call of {symbol}.
    
    Instructions:
    1. Answer the question based ONLY on the provided transcript below.
    2. If the answer is not found in the transcript, strictly say "ข้อมูลนี้ไม่ได้ถูกพูดถึงในการประชุมครั้งนี้ครับ" (or English equivalent).
    3. Keep the answer concise and professional.
    
    Transcript context (partial):
    {text[:25000]} 
    
    User Question: {question}
    """

    completion = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful financial assistant."},
            {"role": "user", "content": prompt},
        ]
    )

    return completion.choices[0].message.content

async def analyze_consistency(symbol: str, text: str) -> ConsistencyResponse:
    print(f"🕵️‍♂️ AI กำลังจับผิดผู้บริหารหุ้น {symbol}...")

    split_markers = ["Question-and-Answer Session", "Questions and Answers", "Q&A"]
    prepared_text = text
    qa_text = ""

    for marker in split_markers:
        if marker in text:
            parts = text.split(marker, 1) 
            prepared_text = parts[0]
            qa_text = parts[1]
            break
    
    if not qa_text:
        qa_text = "No Q&A section detected in this transcript."

    prompt = f"""
    You are a behavioral finance expert. Compare the sentiment between the "Prepared Remarks" (scripted) and the "Q&A Session" (unscripted) for {symbol}.
    
    Data:
    --- PREPARED REMARKS (First 10k chars) ---
    {prepared_text[:10000]}
    
    --- Q&A SESSION (First 10k chars) ---
    {qa_text[:10000]}
    
    Task:
    1. Analyze the sentiment/tone of BOTH sections separately.
    2. Calculate a 'consistency_score': If the tone drops significantly in Q&A (e.g. from Confident to Defensive), this score should be LOW.
    3. Identify any 'red_flag_warning': Did they try to dodge questions? Did the mood change?
    """

    completion = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a cynical financial auditor looking for inconsistencies. Respond in JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format=ConsistencyResponse,
    )

    return completion.choices[0].message.parsed