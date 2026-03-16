from engine import TripMindEngine, Itinerary, DayPlan, Place
from typing import Optional
import time

class MockTripMindEngine(TripMindEngine):
    def __init__(self):
        # We don't initialize real APIs here to save credits
        pass

    def get_exchange_rate(self, target_currency="INR"):
        return 83.5 # Fake conversion rate for testing

    def get_weather_forecast(self, destination: str):
        return {"temp": 24.5, "desc": "Partly Cloudy (Mock Data)"}

    def geocode_place(self, place_name: str, destination: str):
        # Fake coordinates near the equator for testing the map
        return (20.0, 0.0)

    def generate_draft_itinerary(self, destination: str, duration: int, budget: str, interests: str, weather_data: Optional[dict] = None) -> Itinerary:
        """Simulates the Planner Agent with the updated signature."""
        time.sleep(1) 
        return Itinerary(
            days=[
                DayPlan(day_number=i+1, activities=[
                    Place(name=f"Mock Hotel {i+1}", type="Accommodation", description="A cozy mock stay.", estimated_cost_usd=100),
                    Place(name=f"Mock Sight {i+1}", type="Attraction", description="A beautiful mock landmark.", estimated_cost_usd=20),
                    Place(name=f"Mock Cafe {i+1}", type="Food", description="Delicious mock snacks.", estimated_cost_usd=15)
                ]) for i in range(duration)
            ],
            total_estimated_budget=135 * duration
        )

    def verify_places(self, itinerary, destination):
        """Simulates the Verifier Agent."""
        results = []
        for day in itinerary.days:
            for act in day.activities:
                time.sleep(0.1) 
                results.append({"name": act.name, "status": "✅ Verified Real (Mock Mode)"})
        return results

    def chat_with_itinerary(self, user_query: str, itinerary_context: str, chat_history: list):
        """Simulates the Chatbot."""
        time.sleep(0.5)
        return "🤖 This is a mock response from your Dev Mode travel assistant. Your itinerary looks fantastic!"

    def generate_packing_list(self, destination: str, duration: int, weather: Optional[dict], itinerary: Itinerary):
        """Simulates the Packing Agent."""
        return "Clothing: T-shirts, Jeans\nTech: Charger, Powerbank\nDocuments: Passport, Tickets\nToiletries: Toothbrush, Sunscreen"

    def generate_pdf(self, itinerary: Itinerary, destination: str, weather: Optional[dict], rate: float, currency: str):
        """We can just call the real PDF generator since it doesn't cost API credits!"""
        return super().generate_pdf(itinerary, destination, weather, rate, currency)