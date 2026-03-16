import os
import time
import textwrap
import requests
from io import BytesIO
from fpdf import FPDF
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from geopy.geocoders import Nominatim
from dotenv import load_dotenv

load_dotenv()

# --- Data Structures ---
class Place(BaseModel):
    name: str = Field(description="Specific name of the hotel, attraction, or restaurant")
    type: str = Field(description="Must be 'Accommodation', 'Attraction', or 'Food'")
    description: str = Field(description="Why the user should visit")
    estimated_cost_usd: int = Field(description="Estimated cost in USD")

class DayPlan(BaseModel):
    day_number: int
    activities: List[Place]

class Itinerary(BaseModel):
    days: List[DayPlan]
    total_estimated_budget: int

# --- The Multi-Agent Engine ---
class TripMindEngine:
    def __init__(self):
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
        self.search = DuckDuckGoSearchRun()
        self.geolocator = Nominatim(user_agent="tripmind_explorer")

    def get_exchange_rate(self, target_currency="INR"):
        try:
            url = f"https://v6.exchangerate-api.com/v6/{os.getenv('EXCHANGE_API_KEY')}/latest/USD"
            response = requests.get(url).json()
            return response['conversion_rates'].get(target_currency, 1.0)
        except: return 1.0

    def get_weather_forecast(self, destination: str):
        try:
            geo_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_res = requests.get(geo_url, params={"name": destination, "count": 1}).json()
            if "results" in geo_res:
                lat, lon = geo_res["results"][0]["latitude"], geo_res["results"][0]["longitude"]
                w_url = "https://api.open-meteo.com/v1/forecast"
                w_res = requests.get(w_url, params={"latitude": lat, "longitude": lon, "current_weather": True}).json()
                cw = w_res["current_weather"]
                return {"temp": cw["temperature"], "desc": "Clear" if cw["weathercode"] < 3 else "Cloudy/Rainy"}
            return None
        except: return None

    def geocode_place(self, place_name: str, destination: str):
        try:
            time.sleep(1)
            location = self.geolocator.geocode(f"{place_name}, {destination}")
            return (location.latitude, location.longitude) if location else None
        except: return None

    def generate_draft_itinerary(self, destination: str, duration: int, budget: str, interests: str, weather_data: Optional[dict] = None) -> Itinerary:
        structured_llm = self.llm.with_structured_output(Itinerary)
        w_text = f"Weather: {weather_data['temp']}°C ({weather_data['desc']})." if weather_data else ""
        prompt = f"Plan a {duration}-day trip to {destination}. Budget: {budget}. Interests: {interests}. {w_text} Return ONLY valid JSON."
        try: return structured_llm.invoke(prompt)
        except: return structured_llm.invoke(prompt + " Fix JSON.")

    def _verify_single_activity(self, activity, destination):
        try:
            search_result = self.search.invoke(f"{activity.name} {destination}")
            response = self.llm.invoke(f"Is {activity.name} in {destination} real? Info: {search_result[:200]}. Answer YES or NO.")
            status = "✅ Verified Real" if "YES" in str(response.content).upper() else "⚠️ Flagged"
            return {"name": activity.name, "status": status}
        except: return {"name": activity.name, "status": "❓ Failed"}

    def verify_places(self, itinerary: Itinerary, destination: str):
        all_activities = [act for day in itinerary.days for act in day.activities]
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda act: self._verify_single_activity(act, destination), all_activities))
        return results

    def chat_with_itinerary(self, user_query: str, itinerary_context: str, chat_history: list):
        system_msg = f"You are a travel assistant. User's trip: \n{itinerary_context}\nAnswer concisely."
        messages = [{"role": "system", "content": system_msg}] + chat_history + [{"role": "user", "content": user_query}]
        return self.llm.invoke(messages).content

    def generate_packing_list(self, destination: str, duration: int, weather: Optional[dict], itinerary: Itinerary):
        weather_str = f"{weather['temp']}°C, {weather['desc']}" if weather else "Unknown"
        activity_types = list(set([act.type for day in itinerary.days for act in day.activities]))
        prompt = (f"Generate packing list for {duration}-day trip to {destination}. Weather: {weather_str}. "
                  f"Activities: {', '.join(activity_types)}. Categories: Clothing, Tech, Documents, Toiletries. "
                  "Format: CategoryName: item1, item2")
        return self.llm.invoke(prompt).content

    def generate_pdf(self, itinerary: Itinerary, destination: str, weather: Optional[dict], rate: float, currency: str):
        """Bulletproof PDF Generation (Bypasses multi_cell crashes)"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Aggressive text cleaner: Strips ALL non-standard characters to protect the PDF engine
        def safe_text(text):
            return "".join(i for i in str(text) if ord(i) < 128)

        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, safe_text(f"TripMind Itinerary: {destination}"), ln=True, align='C')
        
        pdf.set_font("Arial", size=12)
        if weather:
            pdf.cell(0, 10, safe_text(f"Weather: {weather['temp']}C, {weather['desc']}"), ln=True)
        
        for day in itinerary.days:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, safe_text(f"Day {day.day_number}"), ln=True)
            
            for act in day.activities:
                pdf.set_font("Arial", 'B', 12)
                price = round(act.estimated_cost_usd * rate, 1)
                header_text = safe_text(f"- {act.name} ({act.type}): ~{price} {currency}")
                
                # Manually wrap header text (max 80 characters per line)
                for line in textwrap.wrap(header_text, width=80):
                    pdf.cell(0, 6, line, ln=True)

                pdf.set_font("Arial", 'I', 10)
                desc_text = safe_text(f"  {act.description}")
                
                # Manually wrap description text (max 90 characters per line)
                for line in textwrap.wrap(desc_text, width=90):
                    pdf.cell(0, 5, line, ln=True)
                
                pdf.ln(3) # Small gap between activities

        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        total = round(itinerary.total_estimated_budget * rate, 1)
        pdf.cell(0, 10, safe_text(f"Total Estimated Budget: {total} {currency}"), ln=True)
        
        return bytes(pdf.output())