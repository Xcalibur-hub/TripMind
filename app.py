import streamlit as st
import folium
from streamlit_folium import st_folium
from engine import TripMindEngine
from mock_engine import MockTripMindEngine

st.set_page_config(page_title="TripMind AI", page_icon="✈️", layout="wide")

# Custom Styles
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #FAFAFA; }
    .stButton>button { background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); color: #000; font-weight: bold; border-radius: 30px; }
    </style>
""", unsafe_allow_html=True)

# Engine Logic
st.sidebar.title("Settings")
dev_mode = st.sidebar.toggle("Dev Mode (Mock APIs)", value=True)
if "engine" not in st.session_state or st.session_state.get("last_mode") != dev_mode:
    st.session_state.engine = MockTripMindEngine() if dev_mode else TripMindEngine()
    st.session_state.last_mode = dev_mode

if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "current_itinerary" not in st.session_state: st.session_state.current_itinerary = None

st.title("✈️ TripMind: Multi-Agent Travel Planner")

with st.sidebar:
    st.header("🗺️ Trip Details")
    destination = st.text_input("Destination", "Seoul, South Korea")
    duration = st.slider("Days", 1, 7, 3)
    budget = st.selectbox("Budget Level", ["Moderate", "Luxury", "Backpacker"])
    target_currency = st.selectbox("Currency", ["USD", "INR", "EUR", "GBP", "AED"])
    
    if st.button("🚀 Generate Itinerary", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.generate = True
    else: st.session_state.generate = False

if st.session_state.get("generate") or st.session_state.current_itinerary:
    if st.session_state.generate:
        with st.spinner("🌍 Processing..."):
            st.session_state.current_weather = st.session_state.engine.get_weather_forecast(destination)
            st.session_state.current_itinerary = st.session_state.engine.generate_draft_itinerary(destination, duration, budget, "", st.session_state.current_weather)
            st.session_state.rate = st.session_state.engine.get_exchange_rate(target_currency)
            st.session_state.packing_list = st.session_state.engine.generate_packing_list(destination, duration, st.session_state.current_weather, st.session_state.current_itinerary)

    draft = st.session_state.current_itinerary
    rate = st.session_state.rate
    weather = st.session_state.current_weather
    
    col1, col2 = st.columns([1.5, 1])

    with col1:
        # --- PDF DOWNLOAD (COMMIT 9) ---
        pdf_bytes = st.session_state.engine.generate_pdf(draft, destination, weather, rate, target_currency)
        st.download_button(label="📄 Download Itinerary PDF", data=pdf_bytes, file_name=f"{destination}_trip.pdf", mime="application/pdf")
        
        if weather: st.info(f"🌦️ Weather: {weather['temp']}C, {weather['desc']}")
        
        # UI Elements (Packing, Map, Itinerary)
        with st.expander("🧳 Packing List"):
            st.write(st.session_state.packing_list)

        m = folium.Map(location=[20, 0], zoom_start=2)
        points = []
        for day in draft.days:
            for act in day.activities:
                coords = st.session_state.engine.geocode_place(act.name, destination)
                if coords:
                    folium.Marker(coords, popup=act.name).add_to(m)
                    points.append(coords)
        if points:
            m.fit_bounds(points)
            st_folium(m, width=700, height=300)

        for day in draft.days:
            with st.expander(f"📅 Day {day.day_number}"):
                for act in day.activities:
                    st.write(f"**{act.name}** | ~{round(act.estimated_cost_usd * rate, 1)} {target_currency}")

    with col2:
        st.subheader("🔍 Verification Log")
        log = st.session_state.engine.verify_places(draft, destination)
        for item in log: st.write(f"{item['status']} | {item['name']}")

    # Chat UI
    st.divider()
    st.subheader("💬 Trip Assistant")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if user_input := st.chat_input("Ask a follow-up..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)
        with st.chat_message("assistant"):
            response = st.session_state.engine.chat_with_itinerary(user_input, draft.json(), st.session_state.chat_history[:-1])
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})