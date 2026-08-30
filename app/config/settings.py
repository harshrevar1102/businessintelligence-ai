"""Central configuration for the CafeCo BI prototype.

Everything that would normally live in environment variables, a secrets
manager or a config service is collected here so the rest of the app has
one place to look. Nothing here talks to a database or an LLM directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file: app/config/settings.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

CITIES = ["Ahmedabad", "Jaipur", "Delhi", "Mumbai", "Bengaluru", "Hyderabad"]

STORES = {
    "Ahmedabad": ["Satellite", "Navrangpura"],
    "Jaipur": ["C-Scheme", "Malviya Nagar"],
    "Delhi": ["Connaught Place", "Saket"],
    "Mumbai": ["Bandra", "Andheri"],
    "Bengaluru": ["Indiranagar", "Koramangala"],
    "Hyderabad": ["Banjara Hills", "Gachibowli"],
}

PRODUCTS = ["House Latte", "Cold Brew", "Breakfast Combo", "Cappuccino", "Chai Frappe"]
NEW_PRODUCT = "Chai Frappe"          # launched recently, sparse history
NEW_PRODUCT_LAUNCH_DAYS_AGO = 21

PERSONAS = [
    "CEO / Executive",
    "Regional Manager",
    "Store Manager",
]

# Simulated entitlement, used instead of a real auth system.
# "cities": list of cities the persona can see. None means all of India.
# "store": a single store the persona is pinned to, or None.
# "show_all_india": whether the persona can see the national aggregate.
# "show_cities": whether the persona can see city-level aggregates.
PERSONA_ENTITLEMENTS = {
    "CEO / Executive": {"cities": None, "store": None, "show_all_india": True, "show_cities": True},
    "Regional Manager": {"cities": None, "store": None, "show_all_india": False, "show_cities": True},
    "Store Manager": {"cities": None, "store": None, "show_all_india": False, "show_cities": False},
}

RANDOM_SEED = 42

DATA_HISTORY_DAYS = 120          # how many days of synthetic history to generate
CURRENT_PERIOD_DAYS = 30         # length of the "current" analysis window
BASELINE_LOOKBACK_PERIODS = 3    # how many prior comparable periods form the baseline

MATERIALITY_BUSINESS_IMPACT_INR = 1_000_000   # min absolute INR swing to matter
MATERIALITY_P_VALUE_THRESHOLD = 0.05

CONFIDENCE_THRESHOLDS = {
    "high": 0.75,
    "medium": 0.5,
    "low": 0.25,
}

# --- LLM (OpenAI) configuration ---------------------------------------
# API key must be set in .env file or environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not found in environment variables. LLM features will be disabled.")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", None)
OPENAI_CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
OPENAI_REQUEST_TIMEOUT_SECONDS = 30

# Nominal cost used only to demonstrate cost telemetry. Local Ollama inference
# has no per-token API cost, so this simulates what the same workload would
# cost against a comparable hosted model, purely for the economics panel.
SIMULATED_COST_PER_1K_INPUT_TOKENS_USD = 0.0005
SIMULATED_COST_PER_1K_OUTPUT_TOKENS_USD = 0.0015

RAG_TOP_K = 4
RAG_CHUNK_SIZE_WORDS = 90
RAG_CHUNK_OVERLAP_WORDS = 15

APP_TITLE = "BusinessIntelligence.ai"
APP_SUBTITLE = "CafeCo - India Operations - July 2026"
