# ✈️ TripMind: Multi-Agent Travel Planner

## Project Description
[cite_start]TripMind is an AI-powered travel assistant that generates end-to-end travel itineraries based on user constraints like destination, duration, budget, and interests[cite: 59, 60]. 

Unlike standard LLM wrappers, TripMind utilizes a **Multi-Agent Architecture** to guarantee reliability. [cite_start]It integrates an external search API to cross-reference and verify the ground truth of its own suggestions in real-time, fulfilling the hackathon's objective for integrating real-time data for bonus points[cite: 62].

## Solution Approach
1. **Agent 1 (The Planner):** Uses `llama-3.3-70b-versatile` via Groq to generate a comprehensive draft itinerary.
2. **Agent 2 (The Verifier):** Takes the structured output and queries the DuckDuckGo search API to verify if the suggested locations are real and currently operating.
3. **The Interface:** A custom Streamlit frontend with glassmorphism UI that visually separates the generation and verification phases.

## Prerequisites & Dependencies
* [cite_start]Python 3.9+ [cite: 7, 71]
* Groq API Key
* Dependencies (found in `requirements.txt`): `streamlit`, `langchain-groq`, `langchain-community`, `duckduckgo-search`, `pydantic`, `python-dotenv`.

## Setup and Usage Instructions
1. Clone the repository: `git clone <your-repo-url>`
2. Create and activate a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file and add: `GROQ_API_KEY=your_key_here`
5. Run the app: `streamlit run app.py`