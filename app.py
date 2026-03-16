import streamlit as st
import folium
from streamlit_folium import st_folium
from engine import TripMindEngine
from mock_engine import MockTripMindEngine

st.set_page_config(page_title="TripMind AI", page_icon="✈️", layout="wide")

# Styling
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #FAFAFA; }
    .stButton>button { background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); color: #000; font-weight: bold; border-radius: 30px; }
    </style>
""", unsafe_allow_html=True)

# Engine Init
st.sidebar.title("Settings")
dev_mode = st.sidebar.toggle("Dev Mode (Mock APIs)", value=True)
if "engine" not in st.session_state or st.session_state.get("last_mode") != dev_mode:
    st.session_state.engine = MockTripMindEngine() if dev_mode else TripMindEngine()
    st.session_state.last_mode = dev_mode

st.title("✈️ TripMind: Multi-Agent Travel Planner")

with st.sidebar:
    st.header("🗺️ Trip Details")
    destination = st.text_input("Destination", "Kyoto, Japan")
    duration = st.slider("Days", 1, 7, 3)
    budget = st.selectbox("Budget Level", ["Moderate", "Luxury", "Backpacker"])
    target_currency = st.selectbox("Currency", ["USD", "INR", "EUR", "GBP"])
    generate_btn = st.button("🚀 Generate Itinerary", use_container_width=True)

if generate_btn:
    col1, col2 = st.columns([1.5, 1])
    
    with st.spinner("🌍 Processing..."):
        weather = st.session_state.engine.get_weather_forecast(destination)
        draft = st.session_state.engine.generate_draft_itinerary(destination, duration, budget, "", weather)
        rate = st.session_state.engine.get_exchange_rate(target_currency)

    with col1:
        if weather:
            st.info(f"🌦️ {destination} Weather: {weather['temp']}°C, {weather['desc']}. Agent has adjusted your plan.")

        # --- MAP (COMMIT 5) ---
        st.subheader("📍 Interactive Map")
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

        # --- BREAKDOWN + LINKS (COMMIT 6) ---
        for day in draft.days:
            st.markdown(f"#### 📅 Day {day.day_number}")
            for act in day.activities:
                with st.container():
                    st.write(f"**{act.name}** | ~{round(act.estimated_cost_usd * rate, 1)} {target_currency}")
                    st.caption(act.description)
                    slug = f"{act.name} {destination}".replace(" ", "+")
                    if act.type == "Accommodation":
                        st.link_button("🏨 Book Now", f"https://www.booking.com/search.html?ss={slug}")
                    elif act.type == "Food":
                        st.link_button("🍴 Reviews", f"https://www.tripadvisor.com/Search?q={slug}")
                    else:
                        st.link_button("🗺️ View Maps", f"http://maps.google.com/?q={slug}")
                    st.divider()

    with col2:
        st.subheader("🔍 Verification Log")
        log = st.session_state.engine.verify_places(draft, destination)
        for item in log:
            st.write(f"{item['status']} | {item['name']}")
        st.balloons()