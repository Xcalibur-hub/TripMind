import os
import time
from typing import List
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
        # Using Groq with Llama 3.3 70B for blazing fast multi-agent execution
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
        # Using DuckDuckGo as our free external verification API
        self.search = DuckDuckGoSearchRun()

    def generate_draft_itinerary(self, destination: str, duration: int, budget: str, interests: str) -> Itinerary:
        """Agent 1: The Planner with Robust Parsing"""
        structured_llm = self.llm.with_structured_output(Itinerary)
        
        prompt = (
            f"Generate a {duration}-day itinerary for {destination}. "
            f"Budget: {budget}. Interests: {interests}. "
            "Return ONLY valid JSON. Ensure 'estimated_cost_usd' is an integer."
        )
        
        try:
            return structured_llm.invoke(prompt)
        except Exception as e:
            print(f"⚠️ Initial JSON parse failed: {e}. Triggering fallback...")
            
            fallback_prompt = prompt + " CRITICAL: Please fix the JSON formatting. Output absolutely nothing but valid JSON."
            return structured_llm.invoke(fallback_prompt)

    def verify_places(self, itinerary: Itinerary, destination: str):
        """Agent 2: The Verifier. Hits the web to check if places actually exist."""
        verification_log = []
        
        for day in itinerary.days:
            for activity in day.activities:
                query = f"{activity.name} {activity.type} in {destination} reviews open"
                try:
                    # External API Call to verify ground truth
                    search_result = self.search.invoke(query)
                    
                    # Agentic evaluation of the search result
                    eval_prompt = (
                        f"Based on this web search snippet: '{search_result[:300]}', "
                        f"does the place '{activity.name}' seem to be a real, open business/location? "
                        f"Answer only 'YES' or 'NO'."
                    )
                    
                    response = self.llm.invoke(eval_prompt)
                    raw_content = response.content
                    
                    # Safely extract text whether LangChain returns a list or a string
                    if isinstance(raw_content, list):
                        text_content = raw_content[0].get("text", "") if isinstance(raw_content[0], dict) else str(raw_content[0])
                    else:
                        text_content = str(raw_content)
                        
                    is_real = text_content.strip().upper()
                    
                    status = "✅ Verified Real" if "YES" in is_real else "⚠️ Flagged: Might be closed/fake"
                    verification_log.append({"name": activity.name, "status": status})
                    
                    # Just 1 second to keep DuckDuckGo happy; Groq handles the rest instantly!
                    time.sleep(1) 
                    
                except Exception as e:
                    print(f"💥 ERROR verifying {activity.name}: {e}")
                    verification_log.append({"name": activity.name, "status": "❓ Verification Failed"})
                    time.sleep(1)
                    
        return verification_log