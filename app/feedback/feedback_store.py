"""In-memory feedback capture. Kept in session state, which is enough to
demonstrate the mechanism in a prototype - a real deployment would write
this to a table that a nightly job reads for evaluation/model improvement.
"""

from datetime import datetime

import streamlit as st


def _ensure_store():
    if "feedback_log" not in st.session_state:
        st.session_state.feedback_log = []
    return st.session_state.feedback_log


def submit_feedback(insight_id, persona, verdict, driver_correction=None, comment=None):
    store = _ensure_store()
    entry = {
        "feedback_id": f"FB-USER-{len(store) + 1:04d}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "insight_id": insight_id,
        "persona": persona,
        "verdict": verdict,
        "driver_correction": driver_correction,
        "comment": comment,
    }
    store.append(entry)
    return entry


def get_feedback():
    return _ensure_store()
