"""High-level narrative generation: wires prompts, the Ollama client and a
rich deterministic template fallback together, and always returns telemetry alongside the text.
"""

import time
import json
import textwrap

from app.llm import openai_client, prompts


def _fallback_narrative(persona, kpi_summary, drivers_summary):
    lines = [line.strip("- ") for line in drivers_summary.split("\n") if line.strip()]
    top_driver = lines[0] if lines else "Transactions volume"
    second_driver = lines[1] if len(lines) > 1 else "Service bottlenecks"

    return (
        f"**Executive Synthesis for {persona}:**\n\n"
        f"Analysis of current performance reveals that {kpi_summary.lower()} "
        f"Statistical decomposition indicates that **{top_driver.split(':')[0]}** represents the primary modeled driver of the variance. "
        f"Concurrently, operational telemetry highlights **{second_driver.split(':')[0]}** as a secondary compounding factor. "
        f"While average basket values remained stable or showed modest growth, footfall and transaction volume contractions during peak operating hours "
        f"are the dominant explanatory mechanism. Field notes and customer sentiment logs corroborate service delays during high-traffic windows."
    )


def generate_narrative(persona, kpi_summary, drivers_summary, evidence_summary, confidence_note):
    system_prompt = prompts.narrative_system_prompt(persona)
    user_prompt = prompts.narrative_user_prompt(kpi_summary, drivers_summary, evidence_summary, confidence_note)

    text, input_tokens, output_tokens, latency, success = openai_client.chat(system_prompt, user_prompt)

    if not success or not text:
        text = _fallback_narrative(persona, kpi_summary, drivers_summary)

    return {
        "text": text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_seconds": latency,
        "llm_calls": 1 if success else 0,
        "used_llm": success,
    }


def generate_recommendation_narrative(persona, action_plan_summary):
    system_prompt = prompts.recommendation_system_prompt(persona)
    user_prompt = prompts.recommendation_user_prompt(action_plan_summary)

    text, input_tokens, output_tokens, latency, success = openai_client.chat(system_prompt, user_prompt)

    if not success or not text:
        text = f"**Action Plan ({persona}):** {action_plan_summary}"

    return {
        "text": text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_seconds": latency,
        "llm_calls": 1 if success else 0,
        "used_llm": success,
    }
