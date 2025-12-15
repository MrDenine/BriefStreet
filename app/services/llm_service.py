# app/services/llm_service.py
import json
from openai import OpenAI, OpenAIError
from app.core.config import settings
from app.models.sentiment import AnalysisResponse , ConsistencyResponse
from app.core.exceptions import LLMServiceException
from app.core.decorators import handle_exceptions, retry_on_exception
from app.core.logging_config import get_logger

logger = get_logger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

@retry_on_exception(max_retries=2, exceptions=(OpenAIError,), delay=2.0)
@handle_exceptions(default_exception=LLMServiceException)
def analyze_transcript(symbol: str, text: str) -> AnalysisResponse:
    logger.info(f"🤖 AI analyzing transcript for {symbol} (length: {len(text)} chars)")
    
    if not text or len(text.strip()) == 0:
        logger.error(f"Empty transcript provided for {symbol}")
        raise LLMServiceException(
            message="Cannot analyze empty transcript",
            details={"symbol": symbol}
        )
    
    prompt = f"""
    You are an expert financial analyst. 
    Analyze the following earnings call transcript for {symbol}.
    Extract key highlights, determine the overall sentiment score (0-100), 
    and identify the CEO's tone.
    
    Transcript:
    {text[:15000]}  # ตัด text เพื่อป้องกัน Token เกิน (เบื้องต้น)
    """

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": "You are a helpful financial assistant. Respond in JSON format only."},
                {"role": "user", "content": prompt},
            ],
            response_format=AnalysisResponse, 
        )

        result = completion.choices[0].message.parsed
        logger.info(f"✅ Analysis completed for {symbol} (sentiment: {result.sentiment_score})")
        return result
    except OpenAIError as e:
        logger.error(f"OpenAI error analyzing {symbol}: {str(e)}")
        raise LLMServiceException(
            message=f"OpenAI API error: {str(e)}",
            details={"symbol": symbol, "error_type": type(e).__name__}
        )

@retry_on_exception(max_retries=2, exceptions=(OpenAIError,), delay=2.0)
@handle_exceptions(default_exception=LLMServiceException)
async def chat_with_transcript(symbol: str, text: str, question: str) -> str:
    logger.info(f"💬 User asking about {symbol}: {question[:100]}")
    
    if not text or len(text.strip()) == 0:
        logger.error(f"Empty transcript for chat request on {symbol}")
        raise LLMServiceException(
            message="Cannot chat with empty transcript",
            details={"symbol": symbol}
        )
    
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

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful financial assistant."},
                {"role": "user", "content": prompt},
            ]
        )

        answer = completion.choices[0].message.content
        logger.info(f"✅ Chat response generated for {symbol} (length: {len(answer)} chars)")
        return answer
    except OpenAIError as e:
        logger.error(f"OpenAI chat error for {symbol}: {str(e)}")
        raise LLMServiceException(
            message=f"OpenAI chat error: {str(e)}",
            details={"symbol": symbol, "error_type": type(e).__name__}
        )

@retry_on_exception(max_retries=2, exceptions=(OpenAIError,), delay=2.0)
@handle_exceptions(default_exception=LLMServiceException)
async def analyze_consistency(symbol: str, text: str) -> ConsistencyResponse:
    logger.info(f"🕵️ Analyzing consistency for {symbol}")

    if not text or len(text.strip()) == 0:
        logger.error(f"Empty transcript for consistency analysis on {symbol}")
        raise LLMServiceException(
            message="Cannot analyze consistency of empty transcript",
            details={"symbol": symbol}
        )

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

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a cynical financial auditor looking for inconsistencies. Respond in JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format=ConsistencyResponse,
        )
        
        result = completion.choices[0].message.parsed
        logger.info(f"✅ Consistency analysis completed for {symbol} (score: {result.consistency_score})")
        return result
    except OpenAIError as e:
        logger.error(f"OpenAI consistency error for {symbol}: {str(e)}")
        raise LLMServiceException(
            message=f"OpenAI consistency analysis error: {str(e)}",
            details={"symbol": symbol, "error_type": type(e).__name__}
        )

    return completion.choices[0].message.parsed