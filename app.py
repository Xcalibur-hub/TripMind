import streamlit as st
import folium
from streamlit_folium import st_folium
from engine import TripMindEngine
from mock_engine import MockTripMindEngine

st.set_page_config(page_title="TripMind AI", page_icon="✈️", layout="wide")

# Custom UI
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #FAFAFA; }
    .stButton>button { background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); color: #000; font-weight: bold; border-radius: 30px; }
    .chat-bubble { background: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 15px; margin: 10px 0; border: 1px solid rgba(255,255,255,0.1); }
    </style>
""", unsafe_allow_html=True)

# Engine Init
st.sidebar.title("Settings")
dev_mode = st.sidebar.toggle("Dev Mode (Mock APIs)", value=True)
if "engine" not in st.session_state or st.session_state.get("last_mode") != dev_mode:
    st.session_state.engine = MockTripMindEngine() if dev_mode else TripMindEngine()
    st.session_state.last_mode = dev_mode

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_itinerary" not in st.session_state:
    st.session_state.current_itinerary = None

st.title("✈️ TripMind: Multi-Agent Travel Planner")

with st.sidebar:
    st.header("🗺️ Trip Details")
    destination = st.text_input("Destination", "Kyoto, Japan")
    duration = st.slider("Days", 1, 7, 3)
    budget = st.selectbox("Budget Level", ["Moderate", "Luxury", "Backpacker"])
    target_currency = st.selectbox("Currency", ["USD", "INR", "EUR", "GBP"])
    
    if st.button("🚀 Generate Itinerary", use_container_width=True):
        st.session_state.chat_history = [] # Reset chat for new trip
        st.session_state.generate = True
    else:
        st.session_state.generate = False

if st.session_state.get("generate") or st.session_state.current_itinerary:
    col1, col2 = st.columns([1.5, 1])
    
    if st.session_state.generate:
        with st.spinner("🌍 Gathering Intel..."):
            weather = st.session_state.engine.get_weather_forecast(destination)
            st.session_state.current_itinerary = st.session_state.engine.generate_draft_itinerary(destination, duration, budget, "", weather)
            st.session_state.current_weather = weather
            st.session_state.rate = st.session_state.engine.get_exchange_rate(target_currency)
    
    draft = st.session_state.current_itinerary
    rate = st.session_state.rate
    weather = st.session_state.get("current_weather")

    with col1:
        if weather:
            st.info(f"🌦️ Weather: {weather['temp']}°C, {weather['desc']}. Itinerary optimized.")
        
        # Map Logic
        m = folium.Map(location=[20, 0], zoom_start=2)
        points = []
        for day in draft.days:
            for act in day.activities:
                coords = st.session_state.engine.geocode_place(act.name, destination)
                if coords:
                    color = "blue" if act.type == "Accommodation" else "red" if act.type == "Food" else "green"
                    folium.Marker(coords, popup=act.name, icon=folium.Icon(color=color)).add_to(m)
                    points.append(coords)
        if points:
            m.fit_bounds(points)
            st_folium(m, width=700, height=350)

        # Itinerary
        for day in draft.days:
            with st.expander(f"📅 Day {day.day_number}"):
                for act in day.activities:
                    st.write(f"**{act.name}** | ~{round(act.estimated_cost_usd * rate, 1)} {target_currency}")
                    slug = f"{act.name} {destination}".replace(" ", "+")
                    st.link_button("🏨 View Details", f"http://maps.google.com/?q={slug}")

    with col2:
        st.subheader("🔍 Verification Log")
        log = st.session_state.engine.verify_places(draft, destination)
        for item in log:
            st.write(f"{item['status']} | {item['name']}")

    # --- COMMIT 7: CHAT INTERFACE ---
    st.divider()
    st.subheader("💬 Ask about your trip")
    
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Ask a follow-up question..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                itinerary_str = str(draft.json())
                response = st.session_state.engine.chat_with_itinerary(user_input, itinerary_str, st.session_state.chat_history[:-1])
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})