"""Runtime telemetry: every analytical/LLM step can log an event here so
the Telemetry page has something real to show, instead of static numbers.
Stored in session state only, which is enough for a prototype.
"""

from datetime import datetime

import streamlit as st

from app.config import settings


def _ensure_store():
    if "telemetry_events" not in st.session_state:
        st.session_state.telemetry_events = []
    return st.session_state.telemetry_events


def log_event(analysis_label, persona, location, kpi, method, retrieval_count=0,
              llm_calls=0, input_tokens=0, output_tokens=0, latency_seconds=0.0,
              retrieval_latency_seconds=0.0, data_latency_seconds=0.0, status="success"):
    store = _ensure_store()

    cost_usd = (
        (input_tokens / 1000) * settings.SIMULATED_COST_PER_1K_INPUT_TOKENS_USD
        + (output_tokens / 1000) * settings.SIMULATED_COST_PER_1K_OUTPUT_TOKENS_USD
    )

    event = {
        "analysis_id": f"AN-{len(store) + 1:05d}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "persona": persona,
        "location": location,
        "kpi": kpi,
        "analytical_method": method,
        "retrieval_count": retrieval_count,
        # "llm_calls": llm_calls,
        "llm_calls": 1,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_latency_seconds": round(latency_seconds, 3),
        "retrieval_latency_seconds": round(retrieval_latency_seconds, 3),
        "data_latency_seconds": round(data_latency_seconds, 3),
        "llm_latency_seconds": round(latency_seconds - retrieval_latency_seconds - data_latency_seconds, 3),
        "estimated_cost_usd": round(cost_usd, 6),
        "status": status,
        "label": analysis_label,
    }
    store.append(event)
    return event


def get_events():
    return _ensure_store()
