# app/services/valuation_service.py
import math
from app.services import market_data

async def analyze_valuation(symbol: str) -> dict:
    # 1. ดึงข้อมูลดิบ
    data = await market_data.get_financial_metrics(symbol)
    metrics = data["metrics"]
    price = data["price"]
    cash_flows = data["cash_flows"]
    
    # --- A. DCF Calculation (Simplified) ---
    # สมมติ Growth 5% (ของจริงควรดึง Analyst Estimates หรือคำนวณจากอดีต)
    # สมมติ Discount Rate 10%
    growth_rate = 0.05 
    discount_rate = 0.10
    terminal_growth = 0.02
    
    # ใช้ Free Cash Flow ล่าสุด
    latest_fcf = cash_flows[0].get('freeCashFlow')
    shares_outstanding = metrics.get('netIncomePerShare') # * Hack: หาจำนวนหุ้นคร่าวๆ หรือดึงจาก Enterprise Value
    # เพื่อความแม่นยำควรดึง sharesOutstanding จาก API Quote หรือ Balance Sheet
    
    # (โค้ดคำนวณ DCF แบบย่อ)
    projected_fcf = []
    for i in range(1, 6):
        projected_fcf.append(latest_fcf * ((1 + growth_rate) ** i))
        
    # Discount กลับมา
    dcf_value_sum = sum([fcf / ((1 + discount_rate) ** (i+1)) for i, fcf in enumerate(projected_fcf)])
    
    # Terminal Value
    terminal_val = (projected_fcf[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
    terminal_val_discounted = terminal_val / ((1 + discount_rate) ** 5)
    
    total_enterprise_value = dcf_value_sum + terminal_val_discounted
    # สมมติหารด้วยจำนวนหุ้น (ต้องหาตัวแปร shares มาหาร)
    # intrinsic_price = total_enterprise_value / shares
    intrinsic_price = price * 0.85 # Mock ค่าไปก่อนเพื่อให้เห็นภาพ Logic
    
    dcf_status = "Undervalued" if price < intrinsic_price else "Overvalued"
    margin_safety = ((intrinsic_price - price) / intrinsic_price) * 100

    # --- B. Graham Number ---
    # Formula: Sqrt(22.5 * EPS * BVPS)
    eps = metrics.get('netIncomePerShareTTM', 0)
    bvps = metrics.get('bookValuePerShareTTM', 0)
    
    if eps > 0 and bvps > 0:
        graham_num = math.sqrt(22.5 * eps * bvps)
    else:
        graham_num = 0 # คำนวณไม่ได้ถ้าขาดทุน
        
    graham_status = "Cheap" if price < graham_num else "Expensive"

    # --- C. Relative Valuation (Mock Peer Comparison) ---
    my_pe = metrics.get('peRatioTTM', 0)
    peer_avg_pe = 25.0 # ของจริงต้องดึงคู่แข่งมาหาค่าเฉลี่ย
    
    # --- Construct Response ---
    return {
        "symbol": symbol,
        "current_price": price,
        "dcf": {
            "intrinsic_value": round(intrinsic_price, 2),
            "margin_of_safety": round(margin_safety, 2),
            "status": dcf_status
        },
        "graham": {
            "graham_number": round(graham_num, 2),
            "status": graham_status
        },
        "relative": {
            "stock_pe": round(my_pe, 2),
            "sector_avg_pe": peer_avg_pe,
            "stock_pbv": round(metrics.get('pbRatioTTM', 0), 2),
            "sector_avg_pbv": 4.5,
            "status": "Premium" if my_pe > peer_avg_pe else "Discount"
        },
        "summary": f"DCF suggests {dcf_status}, Graham says {graham_status}."
    }