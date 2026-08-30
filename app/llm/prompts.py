"""Prompt templates. Kept as plain functions rather than a template engine
since the prototype only has a handful of narrative shapes."""

PERSONA_FOCUS = {
    "CEO / Executive": "company-wide performance, major risks, strategic drivers, and expected business impact. Keep it high-level and brief.",
    "CFO / Finance": "revenue, transactions, average ticket and the financial/margin implications. Emphasise numbers and financial risk.",
    "Regional Manager": "regional performance, store comparisons, underperforming locations, and operational drivers within the region.",
    "Store Manager": "store-level performance, staffing, wait time, orders and inventory. Focus on immediate, store-level actions.",
    "Operations Manager": "staffing, wait time, capacity, inventory and operational bottlenecks.",
    "Marketing Manager": "promotions, campaigns, customer segments, conversion and marketing-related drivers.",
    "Business Analyst": "detailed analytical evidence, methodology, driver confidence, source lineage and alternative hypotheses. Be precise and technical.",
}


def narrative_system_prompt(persona):
    focus = PERSONA_FOCUS.get(persona, "overall business performance.")
    return (
        "You are an analyst narrating pre-computed business analytics for CafeCo, an Indian cafe chain. "
        "You are given exact numbers, driver rankings and evidence snippets that have already been "
        "computed by deterministic code. Do not invent numbers, do not contradict the numbers you are "
        f"given, and do not present assumptions as facts. Write for a {persona}, focusing on {focus} "
        "Keep the response to 3-5 short sentences of plain business prose, no headers, no bullet lists, "
        "no markdown."
    )


def narrative_user_prompt(kpi_summary, drivers_summary, evidence_summary, confidence_note):
    return (
        f"KPI movement:\n{kpi_summary}\n\n"
        f"Ranked drivers (already computed, do not recompute):\n{drivers_summary}\n\n"
        f"Supporting evidence snippets:\n{evidence_summary}\n\n"
        f"Confidence note:\n{confidence_note}\n\n"
        "Write the narrative now."
    )


def recommendation_system_prompt(persona):
    return (
        f"You are writing a one-paragraph recommendation for a {persona} at CafeCo. "
        "You are given a specific driver, lever, action, expected impact, owner, confidence and "
        "monitoring plan that have already been decided. Restate them as natural, persuasive business "
        "prose in 2-3 sentences. Do not change the numbers, owner or confidence level you are given."
    )


def recommendation_user_prompt(action_plan_summary):
    return f"Recommendation details:\n{action_plan_summary}\n\nWrite the recommendation now."
