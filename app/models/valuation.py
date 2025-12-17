# app/models/valuation.py
from pydantic import BaseModel, Field
from typing import List, Optional

class DCFAnalysis(BaseModel):
    intrinsic_value: float = Field(description="มูลค่าที่แท้จริงจากการคำนวณ DCF")
    margin_of_safety: float = Field(description="ส่วนต่างราคาตลาดกับมูลค่าจริง (%)")
    status: str = Field(description="Undervalued / Overvalued / Fair")

class GrahamAnalysis(BaseModel):
    graham_number: float
    status: str

class RelativeAnalysis(BaseModel):
    stock_pe: float
    sector_avg_pe: float
    stock_pbv: float
    sector_avg_pbv: float
    status: str

class ValuationResponse(BaseModel):
    symbol: str
    current_price: float
    dcf: DCFAnalysis
    graham: GrahamAnalysis
    relative: RelativeAnalysis
    summary: str = Field(description="สรุปคำแนะนำสั้นๆ เช่น 'Buy for Deep Value'")