"""Thin wrapper around the OpenAI Python SDK.

Only used for narrative generation and evidence interpretation - never
for the underlying KPI numbers. If the API is unreachable, calls fail fast
and callers fall back to a template-based narrative so the rest of the
prototype still works end to end.
"""

import time
from openai import OpenAI

from app.config import settings


def _get_client():
    kwargs = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL
    return OpenAI(**kwargs)


def is_available():
    try:
        client = _get_client()
        # Just check if we can list models as a connection test
        client.models.list(timeout=3)
        return True
    except Exception:
        return False


def chat(system_prompt, user_prompt, model=None, temperature=0.3):
    """Returns (text, input_tokens_est, output_tokens_est, latency_seconds, success)."""
    model = model or settings.OPENAI_CHAT_MODEL
    start = time.time()

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            timeout=settings.OPENAI_REQUEST_TIMEOUT_SECONDS,
        )
        
        text = response.choices[0].message.content.strip()
        latency = time.time() - start

        input_tokens = response.usage.prompt_tokens if response.usage else _estimate_tokens(system_prompt + user_prompt)
        output_tokens = response.usage.completion_tokens if response.usage else _estimate_tokens(text)

        return text, input_tokens, output_tokens, latency, True
    except Exception as e:
        import traceback
        print(f"[openai_client] API call failed: {e}")
        traceback.print_exc()
        latency = time.time() - start
        return "", _estimate_tokens(system_prompt + user_prompt), 0, latency, False


def _estimate_tokens(text):
    return max(1, int(len(text.split()) * 1.3))
