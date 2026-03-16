import streamlit as st
from engine import TripMindEngine
from mock_engine import MockTripMindEngine
import time

st.set_page_config(page_title="TripMind AI", page_icon="✈️", layout="wide")

# --- CUSTOM CSS FOR BEAUTIFUL UI ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: #FAFAFA;
    }
    .stButton>button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: #000000;
        font-weight: bold;
        border: none;
        border-radius: 30px;
        padding: 10px 24px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 201, 255, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 6px 20px rgba(146, 254, 157, 0.6);
    }
    [data-testid="stSidebar"] {
        background-color: rgba(15, 32, 39, 0.6) !important;
        backdrop-filter: blur(10px);
    }
    </style>
""", unsafe_allow_html=True)

# --- ENGINE INITIALIZATION WITH DEV MODE ---
st.sidebar.title("Settings")
dev_mode = st.sidebar.toggle("Dev Mode (Mock APIs)", value=True)

# Logic to switch engine types based on toggle
if "engine" not in st.session_state or "last_mode" not in st.session_state or st.session_state.last_mode != dev_mode:
    if dev_mode:
        st.session_state.engine = MockTripMindEngine()
    else:
        st.session_state.engine = TripMindEngine()
    st.session_state.last_mode = dev_mode

# --- UI CONTENT ---
st.title("✈️ TripMind: Multi-Agent Travel Planner")
st.markdown("*Reliable travel planning powered by Multi-Agent Verification.*")

with st.sidebar:
    st.header("🗺️ Trip Details")
    destination = st.text_input("Destination", "Kyoto, Japan")
    duration = st.slider("Days", 1, 7, 3)
    budget = st.selectbox("Budget Level", ["Backpacker (Cheap)", "Moderate", "Luxury"])
    interests = st.text_area("Interests", "Hidden shrines, matcha tea, street food")
    st.divider()
    generate_btn = st.button("🚀 Generate & Verify Itinerary", use_container_width=True)

if generate_btn:
    if dev_mode:
        st.warning("⚠️ Running in Dev Mode (Mock Data). No API credits being used.")
        
    col1, col2 = st.columns([1.5, 1])
    
    with st.spinner("🤖 Agent 1 (Planner) is drafting..."):
        draft = st.session_state.engine.generate_draft_itinerary(destination, duration, budget, interests)
    
    with col1:
        st.subheader(f"✨ Your {duration}-Day Itinerary")
        st.metric(label="Estimated Total Cost", value=f"${draft.total_estimated_budget} USD")
        
        for day in draft.days:
            with st.expander(f"📅 Day {day.day_number}", expanded=True):
                for act in day.activities:
                    st.markdown(f"**{act.name}** ({act.type}) • ~${act.estimated_cost_usd}")
                    st.caption(f"↳ *{act.description}*")
                    
    with col2:
        st.subheader("🔍 Agent 2: Live Verification")
        st.info("Cross-referencing web data...")
        
        with st.spinner("Verifying locations..."):
            log = st.session_state.engine.verify_places(draft, destination)
            
            for item in log:
                if "✅" in item["status"]:
                    st.success(f"**{item['name']}**\n{item['status']}")
                else:
                    st.error(f"**{item['name']}**\n{item['status']}")
            st.balloons()