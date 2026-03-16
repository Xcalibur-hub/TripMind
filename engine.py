import os
import time
import requests
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
        """FREE Weather Forecast using Open-Meteo (Commit 4)"""
        try:
            # 1. Get Coordinates (Geocoding API)
            geo_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_res = requests.get(geo_url, params={"name": destination, "count": 1}).json()
            
            if "results" in geo_res:
                lat = geo_res["results"][0]["latitude"]
                lon = geo_res["results"][0]["longitude"]
                
                # 2. Get Current Weather (Forecast API)
                weather_url = "https://api.open-meteo.com/v1/forecast"
                weather_params = {"latitude": lat, "longitude": lon, "current_weather": True}
                w_res = requests.get(weather_url, params=weather_params).json()
                
                if "current_weather" in w_res:
                    cw = w_res["current_weather"]
                    return {
                        "temp": cw["temperature"],
                        "code": cw["weathercode"], # WMO codes like 0 (clear), 61 (rain)
                        "desc": "Clear Skies" if cw["weathercode"] == 0 else "Cloudy/Rainy" if cw["weathercode"] > 50 else "Partly Cloudy"
                    }
            return None
        except Exception as e:
            print(f"Weather Error: {e}")
            return None

    def geocode_place(self, place_name: str, destination: str):
        try:
            time.sleep(1) # Respect Nominatim usage
            location = self.geolocator.geocode(f"{place_name}, {destination}")
            return (location.latitude, location.longitude) if location else None
        except: return None

    def generate_draft_itinerary(self, destination: str, duration: int, budget: str, interests: str, weather_data: Optional[dict] = None) -> Itinerary:
        """Agentic Adjustment: LLM reacts to weather context"""
        structured_llm = self.llm.with_structured_output(Itinerary)
        
        weather_context = ""
        if weather_data:
            weather_context = f"Context: It is currently {weather_data['temp']}°C with {weather_data['desc']}. "
            if "Rain" in weather_data['desc']:
                weather_context += "Prioritize indoor activities."

        prompt = (
            f"Generate a {duration}-day itinerary for {destination}. Budget: {budget}. Interests: {interests}. {weather_context} "
            "Return ONLY valid JSON. Ensure 'estimated_cost_usd' is an integer."
        )
        try:
            return structured_llm.invoke(prompt)
        except:
            return structured_llm.invoke(prompt + " Fix JSON.")

    def _verify_single_activity(self, activity, destination):
        try:
            search_result = self.search.invoke(f"{activity.name} {destination}")
            response = self.llm.invoke(f"Is {activity.name} in {destination} real? Search snippet: {search_result[:200]}. Answer YES or NO.")
            status = "✅ Verified Real" if "YES" in str(response.content).upper() else "⚠️ Flagged"
            return {"name": activity.name, "status": status}
        except: return {"name": activity.name, "status": "❓ Failed"}

    def verify_places(self, itinerary: Itinerary, destination: str):
        all_activities = [act for day in itinerary.days for act in day.activities]
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda act: self._verify_single_activity(act, destination), all_activities))
        return results