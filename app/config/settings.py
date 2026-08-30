"""Central configuration for the CafeCo BI prototype.

Everything that would normally live in environment variables, a secrets
manager or a config service is collected here so the rest of the app has
one place to look. Nothing here talks to a database or an LLM directly.
"""

import os

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
    "CFO / Finance",
    "Regional Manager",
    "Store Manager",
    "Operations Manager",
    "Marketing Manager",
    "Business Analyst",
]

# Simulated entitlement, used instead of a real auth system.
# "cities": list of cities the persona can see. None means all of India.
# "store": a single store the persona is pinned to, or None.
PERSONA_ENTITLEMENTS = {
    "CEO / Executive": {"cities": None, "store": None},
    "CFO / Finance": {"cities": None, "store": None},
    "Regional Manager": {"cities": ["Mumbai"], "store": None},
    "Store Manager": {"cities": ["Mumbai"], "store": "Bandra"},
    "Operations Manager": {"cities": None, "store": None},
    "Marketing Manager": {"cities": None, "store": None},
    "Business Analyst": {"cities": None, "store": None},
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

# --- LLM (Ollama) configuration ---------------------------------------
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "llama3.1:8b")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_REQUEST_TIMEOUT_SECONDS = 30

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
