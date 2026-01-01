# dashboard.py
import streamlit as st
import requests
import time
from datetime import datetime

# ตั้งค่า API URL
API_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="BriefStreet Bot Control", page_icon="🤖", layout="wide")

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

st.title("🤖 BriefStreet Bot Commander")
st.caption("จัดการ Trading Bots ทั้งหมดในที่เดียว")

# --- System Status Bar ---
try:
    res = requests.get(f"{API_URL}/bot/status", timeout=2)
    if res.status_code == 200:
        st.success("🟢 API Online | Scheduler: Active")
    else:
        st.warning("🔴 API Offline")
except:
    st.error("🔴 Cannot connect to API")

st.divider()

# --- ส่วนที่ 1: Create New Bot ---
st.subheader("➕ Create New Bot")

with st.form("create_bot_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_symbol = st.text_input("Symbol (เช่น BTC/USDT)", placeholder="BTC/USDT")
    
    with col2:
        strategy = st.selectbox("Strategy", ["Mock_Test", "Mean_Reversion", "Momentum"])
    
    with col3:
        trade_amount = st.number_input("Trade Amount (USDT)", min_value=1, value=10, step=5)
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        submit = st.form_submit_button("🚀 Create Bot", type="primary", use_container_width=True)
    
    if submit and new_symbol:
        with st.spinner(f'Creating bot for {new_symbol}...'):
            try:
                payload = {
                    "symbol": new_symbol,
                    "strategy_name": strategy,
                    "parameters": {
                        "trade_amount": trade_amount,
                        "force_buy": False
                    },
                    "is_active": False
                }
                response = requests.post(f"{API_URL}/bot/bots", json=payload, timeout=5)
                
                if response.status_code == 200:
                    st.success(f"✅ Bot created for {new_symbol}!")
                    st.session_state.last_update = time.time()
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ {response.json().get('detail', 'Failed to create bot')}")
            except Exception as e:
                st.error(f"Error: {e}")
    elif submit:
        st.warning("Please enter a symbol")

# --- ส่วนที่ 2: Bot Management ---
st.divider()

col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
with col_header1:
    st.subheader("🤖 Active Bots")
with col_header2:
    auto_refresh = st.checkbox("🔄 Auto Refresh (5s)", value=False)
with col_header3:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.session_state.last_update = time.time()
        st.rerun()

# Auto-refresh logic
if auto_refresh:
    time_since_update = time.time() - st.session_state.last_update
    if time_since_update > 5:
        st.session_state.last_update = time.time()
        st.rerun()

# ดึงรายการ Bots
try:
    response = requests.get(f"{API_URL}/bot/bots", timeout=5)
    if response.status_code == 200:
        data = response.json()
        bots = data.get("bots", [])
        
        if not bots:
            st.info("ℹ️ No bots configured. Create one above!")
        else:
            # แสดงแต่ละ Bot เป็น Card
            for bot in bots:
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1.5, 1, 1, 1])
                    
                    with col1:
                        status_icon = "🟢" if bot["is_active"] else "⚫"
                        st.write(f"### {status_icon} {bot['symbol']}")
                    
                    with col2:
                        st.write(f"**Strategy:** {bot['strategy_name']}")
                    
                    with col3:
                        last_action = bot.get('last_action', 'N/A')
                        st.write(f"**Last:** {last_action}")
                    
                    # ปุ่ม Start
                    with col4:
                        if not bot["is_active"]:
                            if st.button("▶️ Start", key=f"start_{bot['symbol']}", use_container_width=True):
                                try:
                                    res = requests.patch(f"{API_URL}/bot/bots/{bot['symbol']}/start", timeout=5)
                                    if res.status_code == 200:
                                        st.session_state.last_update = time.time()
                                        st.toast(f"✅ Started {bot['symbol']}", icon="✅")
                                    else:
                                        st.error(f"Failed: {res.text}")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        else:
                            st.button("▶️ Start", disabled=True, key=f"start_{bot['symbol']}", use_container_width=True)
                    
                    # ปุ่ม Stop
                    with col5:
                        if bot["is_active"]:
                            if st.button("⏸️ Stop", key=f"stop_{bot['symbol']}", use_container_width=True):
                                try:
                                    res = requests.patch(f"{API_URL}/bot/bots/{bot['symbol']}/stop", timeout=5)
                                    if res.status_code == 200:
                                        st.session_state.last_update = time.time()
                                        st.toast(f"⏸️ Stopped {bot['symbol']}", icon="⏸️")
                                    else:
                                        st.error(f"Failed: {res.text}")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        else:
                            st.button("⏸️ Stop", disabled=True, key=f"stop_{bot['symbol']}", use_container_width=True)
                    
                    # ปุ่ม Delete
                    with col6:
                        if st.button("🗑️ Del", key=f"delete_{bot['symbol']}", use_container_width=True):
                            try:
                                res = requests.delete(f"{API_URL}/bot/bots/{bot['symbol']}", timeout=5)
                                if res.status_code == 200:
                                    st.session_state.last_update = time.time()
                                    st.toast(f"🗑️ Deleted {bot['symbol']}", icon="🗑️")
                                else:
                                    st.error(f"Failed: {res.text}")
                            except Exception as e:
                                st.error(f"Error: {e}")
                    
                    st.divider()
    else:
        st.error("Failed to load bots")
        
except Exception as e:
    st.error(f"Connection Error: {e}")

# --- ส่วนที่ 3: Manual Trigger ---
st.divider()
st.subheader("⚡ Manual Actions")

col_manual1, col_manual2 = st.columns([3, 1])
with col_manual1:
    if st.button("🚀 Run All Active Bots Now", type="primary", use_container_width=True):
        with st.spinner("Triggering bot cycle..."):
            try:
                response = requests.post(f"{API_URL}/bot/run-now", timeout=5)
                
                if response.status_code == 200:
                    st.success("✅ Bot cycle started in background!")
                else:
                    st.error(f"Failed: {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

with col_manual2:
    st.metric("Last Update", f"{int(time.time() - st.session_state.last_update)}s ago")
