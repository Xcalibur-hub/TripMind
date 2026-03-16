from engine import TripMindEngine, Itinerary, DayPlan, Place
import time

class MockTripMindEngine(TripMindEngine):
    def __init__(self):
        # We don't initialize the real LLM or Search tool here
        pass

    def generate_draft_itinerary(self, destination: str, duration: int, budget: str, interests: str) -> Itinerary:
        """Simulates the Planner Agent instantly without an API call."""
        time.sleep(1) # Simulate a slight 'thinking' delay
        return Itinerary(
            days=[
                DayPlan(day_number=1, activities=[
                    Place(name="Mock Hotel", type="Accommodation", description="A fake cozy stay.", estimated_cost_usd=100),
                    Place(name="Mock Museum", type="Attraction", description="A fake historical site.", estimated_cost_usd=20)
                ])
            ],
            total_estimated_budget=120
        )

    def verify_places(self, itinerary, destination):
        """Simulates the Verifier Agent hitting the search API."""
        results = []
        for day in itinerary.days:
            for act in day.activities:
                # This tests your 'Concurrent' logic if you've implemented Commit 2!
                time.sleep(0.5) 
                results.append({"name": act.name, "status": "✅ Verified Real (Mock Mode)"})
        return results