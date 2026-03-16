import streamlit as st
from engine import TripMindEngine
from mock_engine import MockTripMindEngine

st.set_page_config(page_title="TripMind AI", page_icon="✈️", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #FAFAFA; }
    .stButton>button { background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); color: #000; font-weight: bold; border-radius: 30px; }
    </style>
""", unsafe_allow_html=True)

# Engine Initialization
st.sidebar.title("Settings")
dev_mode = st.sidebar.toggle("Dev Mode (Mock APIs)", value=True)

if "engine" not in st.session_state or st.session_state.get("last_mode") != dev_mode:
    st.session_state.engine = MockTripMindEngine() if dev_mode else TripMindEngine()
    st.session_state.last_mode = dev_mode

# UI Layout
st.title("✈️ TripMind: Multi-Agent Travel Planner")

with st.sidebar:
    st.header("🗺️ Trip Details")
    destination = st.text_input("Destination", "Kyoto, Japan")
    duration = st.slider("Days", 1, 7, 3)
    budget = st.selectbox("Budget Level", ["Backpacker", "Moderate", "Luxury"])
    interests = st.text_area("Interests", "Culture, Food")
    
    # NEW: Currency Selector (Commit 3)
    st.divider()
    target_currency = st.selectbox("Display Currency", ["USD", "INR", "EUR", "GBP", "AED", "SGD"])
    
    generate_btn = st.button("🚀 Generate Itinerary", use_container_width=True)

if generate_btn:
    col1, col2 = st.columns([1.5, 1])
    
    with st.spinner("🤖 Planning..."):
        draft = st.session_state.engine.generate_draft_itinerary(destination, duration, budget, interests)
        # Fetch Conversion Rate
        rate = st.session_state.engine.get_exchange_rate(target_currency)
    
    with col1:
        st.subheader(f"✨ Your {duration}-Day Trip")
        
        # Display converted cost
        total_converted = round(draft.total_estimated_budget * rate, 2)
        st.metric(label=f"Total Budget ({target_currency})", value=f"{total_converted} {target_currency}")
        
        for day in draft.days:
            with st.expander(f"📅 Day {day.day_number}", expanded=True):
                for act in day.activities:
                    local_price = round(act.estimated_cost_usd * rate, 2)
                    st.markdown(f"**{act.name}** • ~{local_price} {target_currency}")
                    st.caption(f"↳ {act.description}")
                    
    with col2:
        st.subheader("🔍 Verification Log")
        with st.spinner("Verifying..."):
            log = st.session_state.engine.verify_places(draft, destination)
            for item in log:
                if "✅" in item["status"]: st.success(f"{item['name']}: Verified")
                else: st.error(f"{item['name']}: Check manually")
            st.balloons()