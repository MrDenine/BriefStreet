import streamlit as st
import requests
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURATION ---
API_BASE_URL = "http://localhost:8000/api/v1"
st.set_page_config(page_title="BriefStreet Trader", layout="wide", page_icon="📈")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .signal-buy { color: #00ff00; font-weight: bold; }
    .signal-wait { color: #ffcc00; font-weight: bold; }
    .signal-sell { color: #ff0000; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SCANNER & SETTINGS ---
with st.sidebar:
    st.title("🔍 BriefStreet Scanner")
    st.caption("เครื่องมือสแกนหาหุ้นต้นน้ำ")
    
    scan_preset = st.selectbox("เลือกกลุ่มหุ้น (Preset)", ["CRYPTO_TOP", "TECH_GIANTS"])
    target_signal = st.selectbox("กรองสัญญาณ", ["BUY_DIP", "SELL_RALLY", "WAIT"])
    
    if st.button("🚀 สแกนตลาดเดี๋ยวนี้", use_container_width=True):
        with st.spinner("กำลังสแกนตลาด..."):
            try:
                # ยิง API ไปที่ Scanner Endpoint
                payload = {"preset": scan_preset, "signal_filter": target_signal}
                response = requests.post(f"{API_BASE_URL}/technical/scan", params=payload)
                
                if response.status_code == 200:
                    results = response.json()
                    if results:
                        st.success(f"เจอ {len(results)} ตัวที่เข้าเงื่อนไข!")
                        for res in results:
                            # แสดงผลลัพธ์แบบ Card ย่อๆ
                            with st.expander(f"{res['symbol']} ({res['trend']})"):
                                st.write(f"RSI: {res['rsi']}")
                                st.write(f"Signal: {res['signal']}")
                                if st.button(f"ดูวิเคราะห์ {res['symbol']}", key=f"btn_{res['symbol']}"):
                                    st.session_state.selected_symbol = res['symbol']
                                    st.rerun()
                    else:
                        st.warning("ไม่พบหุ้นที่ตรงตามเงื่อนไข")
                else:
                    st.error("เชื่อมต่อ API ไม่ได้")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    st.subheader("⚙️ Settings")
    history_days = st.slider("จำนวนวันย้อนหลัง (กราฟ)", 60, 365, 180)

# --- MAIN CONTENT ---
st.title("📈 BriefStreet Dashboard")

# 1. SEARCH BAR
if "selected_symbol" not in st.session_state:
    st.session_state.selected_symbol = "BTC-USD"

col_search, col_btn = st.columns([3, 1])
with col_search:
    symbol_input = st.text_input("พิมพ์ชื่อหุ้น / เหรียญ (เช่น NVDA, ETH-USD)", value=st.session_state.selected_symbol)
with col_btn:
    st.write("") # Spacer
    st.write("") 
    if st.button("Analyze", use_container_width=True):
        st.session_state.selected_symbol = symbol_input.upper()
        st.rerun()

symbol = st.session_state.selected_symbol

# --- FETCH DATA & VISUALIZE ---
try:
    # A. เรียก API หลังบ้านเพื่อเอา "สัญญาณ" และ "ราคาปัจจุบัน"
    api_res = requests.get(f"{API_BASE_URL}/technical/{symbol}")
    
    if api_res.status_code == 200:
        data = api_res.json()
        
        # B. แสดง Metrics หลัก
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("ราคาปัจจุบัน", f"${data['current_price']:,.2f}")
        m2.metric("เทรนด์หลัก (EMA200)", data['trend'], 
                  delta="ขาขึ้น" if data['trend'] == "UPTREND" else "ขาลง")
        m3.metric("RSI (Momentum)", data['rsi'], 
                  delta=data['rsi'] - 50, delta_color="inverse") # RSI ต่ำๆ สีเขียว (oversold)
        
        signal_color = "green" if data['signal'] == "BUY_DIP" else "red" if data['signal'] == "SELL_RALLY" else "orange"
        m4.markdown(f"### Signal: <span style='color:{signal_color}'>{data['signal']}</span>", unsafe_allow_html=True)
        
        st.info(f"🛑 แนวรับ: {data['support_levels']} | 🚧 แนวต้าน: {data['resistance_levels']}")

        # C. แสดงกราฟ (Visual Debugger)
        # หมายเหตุ: เราดึง yfinance ตรงนี้เพื่อวาดกราฟให้เห็นภาพ (จำลอง Logic เดียวกับหลังบ้าน)
        st.subheader(f"📊 Visual Analysis: {symbol}")
        
        with st.spinner("กำลังโหลดกราฟ..."):
            df = yf.download(symbol, period=f"{history_days}d", interval="1d", progress=False)

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if not df.empty:
                # คำนวณ Indicator (Logic เดียวกับ Backend)
                df['EMA_50'] = ta.ema(df['Close'], length=50) 
                df['EMA_200'] = ta.ema(df['Close'], length=200)
                df['RSI'] = ta.rsi(df['Close'], length=14)

                # สร้างกราฟ 2 ชั้น (Price & RSI)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.05, row_heights=[0.7, 0.3])

                # 1. Candlestick
                fig.add_trace(go.Candlestick(x=df.index,
                                open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
                
                # 2. EMA Lines
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='orange', width=1), name="EMA 50"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='blue', width=2), name="EMA 200"), row=1, col=1)

                # 3. RSI
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name="RSI"), row=2, col=1)
                
                # Zones
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hrect(y0=0, y1=45, fillcolor="green", opacity=0.1, line_width=0, row=2, col=1, annotation_text="Buy Zone")

                # Highlight จุดซื้อ (ลูกศร)
                # Logic: Price > EMA50 AND RSI < 45
                buy_signals = df[(df['Close'] > df['EMA_50']) & (df['RSI'] < 45)]
                if not buy_signals.empty:
                    fig.add_trace(go.Scatter(
                        x=buy_signals.index, y=buy_signals['Low']*0.98,
                        mode='markers', marker=dict(symbol='triangle-up', size=12, color='green'),
                        name='Potential BUY'
                    ), row=1, col=1)

                fig.update_layout(height=600, xaxis_rangeslider_visible=False, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.error(f"ไม่พบข้อมูล {symbol} หรือระบบหลังบ้านมีปัญหา")

except Exception as e:
    st.error(f"Connection Error: {e}")


# --- AI MENTOR CHAT ---
st.divider()
st.subheader(f"💬 คุยกับ AI Mentor เกี่ยวกับ {symbol}")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดง Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ช่องพิมพ์ข้อความ
if prompt := st.chat_input(f"ถามเกี่ยวกับ {symbol} (เช่น 'น่าเข้าตรงไหน', 'แนวโน้มเป็นไง')..."):
    # 1. แสดงข้อความ User
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. เรียก API AI Backend
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            with st.spinner("AI กำลังวิเคราะห์กราฟ..."):
                payload = {"question": prompt}
                # เรียก Endpoint Chat Technical ที่เราเพิ่งทำ
                chat_res = requests.post(f"{API_BASE_URL}/chat/technical/{symbol}", json=payload)
                
                if chat_res.status_code == 200:
                    full_response = chat_res.json()['answer']
                    message_placeholder.markdown(full_response)
                else:
                    message_placeholder.error("AI ตอบกลับไม่ได้ในขณะนี้")
        except Exception as e:
            message_placeholder.error(f"Error: {e}")
            
    # 3. บันทึกคำตอบลง History
    st.session_state.messages.append({"role": "assistant", "content": full_response})