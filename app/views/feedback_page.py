import textwrap
import pandas as pd
import streamlit as st

from app.components.ui_helpers import section_header
from app.feedback.feedback_store import get_feedback, submit_feedback


def render(datasets, persona, location_label):
    section_header(
        "Submit Feedback on an Insight",
        "Record qualitative ratings or corrections on automated causal findings.",
    )

    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            insight_id = st.text_input(
                "Insight Reference ID",
                value=f"EXEC-{location_label}-Revenue",
            )
        with c2:
            verdict = st.selectbox(
                "Verdict",
                [
                    "Correct",
                    "Partially correct",
                    "Incorrect",
                    "Helpful",
                    "Not helpful",
                    "Driver was wrong",
                    "Recommendation was useful",
                    "Recommendation was not useful",
                ],
            )

        driver_correction = st.text_input("Correct Driver Name (optional if 'Driver was wrong')")
        comment = st.text_area("Detailed Feedback or Context (optional)")

        if st.button("Submit Feedback", type="primary"):
            submit_feedback(insight_id, persona, verdict, driver_correction or None, comment or None)
            st.success("Feedback successfully recorded.")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    section_header("Session Feedback History", "Audit log of human-in-the-loop annotations recorded in this session.")
    
    with st.container(border=True):
        log = get_feedback()
        if log:
            st.dataframe(pd.DataFrame(log), use_container_width=True, hide_index=True)
        else:
            st.markdown("<div style='color:#475569;font-size:13px;'>No feedback submitted yet in this session.</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    section_header("Production Feedback Loop Architecture")
    
    with st.container(border=True):
        st.markdown(
            textwrap.dedent("""
<div style="font-size:13.5px;color:#1e293b;line-height:1.6;font-weight:500;">
<ul style="margin:0;padding-left:18px;">
<li><b>Evaluation</b>: Verdicts feed a running accuracy score per driver and per persona narrative template.</li>
<li><b>Driver Ranking Tuning</b>: Repeated "driver was wrong" corrections automatically down-weight that driver's business rule or correlation weight for similar scopes.</li>
<li><b>LLM Prompt Refinement</b>: Analyst corrections are aggregated into few-shot context examples to align narrative generation.</li>
<li><b>Action Validation</b>: Recommendations flagged as "not useful" trigger review by operational domain owners.</li>
</ul>
</div>
""").strip(),
            unsafe_allow_html=True,
        )
