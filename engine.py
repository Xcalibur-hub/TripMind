import os
import time
import requests
from typing import List
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv

load_dotenv()

# --- Data Structures for Structured Output ---
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

    def get_exchange_rate(self, target_currency="INR"):
        """Fetch live exchange rates from USD to Target (Commit 3)"""
        try:
            api_key = os.getenv("EXCHANGE_API_KEY")
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
            response = requests.get(url).json()
            if response.get("result") == "success":
                return response['conversion_rates'].get(target_currency, 1.0)
            return 1.0
        except Exception as e:
            print(f"Currency Error: {e}")
            return 1.0

    def generate_draft_itinerary(self, destination: str, duration: int, budget: str, interests: str) -> Itinerary:
        """Agent 1: The Planner"""
        structured_llm = self.llm.with_structured_output(Itinerary)
        prompt = (
            f"Generate a {duration}-day itinerary for {destination}. "
            f"Budget: {budget}. Interests: {interests}. "
            "Return ONLY valid JSON. Ensure 'estimated_cost_usd' is an integer."
        )
        try:
            return structured_llm.invoke(prompt)
        except Exception:
            return structured_llm.invoke(prompt + " Please fix the JSON formatting.")

    def _verify_single_activity(self, activity, destination):
        """Helper for concurrency"""
        query = f"{activity.name} {activity.type} in {destination} reviews open"
        try:
            search_result = self.search.invoke(query)
            eval_prompt = f"Is '{activity.name}' in {destination} a real, open business based on: {search_result[:300]}? Answer YES or NO."
            response = self.llm.invoke(eval_prompt)
            is_real = str(response.content).strip().upper()
            status = "✅ Verified Real" if "YES" in is_real else "⚠️ Flagged: Might be closed/fake"
            return {"name": activity.name, "status": status}
        except:
            return {"name": activity.name, "status": "❓ Verification Failed"}

    def verify_places(self, itinerary: Itinerary, destination: str):
        """Agent 2: The Verifier (Concurrent)"""
        all_activities = [act for day in itinerary.days for act in day.activities]
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda act: self._verify_single_activity(act, destination), all_activities))
        return results