"""Thin wrapper around the local Ollama server.

Only used for narrative generation and evidence interpretation - never
for the underlying KPI numbers. If Ollama isn't running, calls fail fast
and callers fall back to a template-based narrative so the rest of the
prototype still works end to end.
"""

import time

import requests

from app.config import settings


def is_available():
    try:
        resp = requests.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def chat(system_prompt, user_prompt, model=None, temperature=0.3):
    """Returns (text, input_tokens_est, output_tokens_est, latency_seconds, success)."""
    model = model or settings.OLLAMA_CHAT_MODEL
    start = time.time()

    try:
        resp = requests.post(
            f"{settings.OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=settings.OLLAMA_REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data.get("message", {}).get("content", "").strip()
        latency = time.time() - start

        input_tokens = data.get("prompt_eval_count") or _estimate_tokens(system_prompt + user_prompt)
        output_tokens = data.get("eval_count") or _estimate_tokens(text)

        return text, input_tokens, output_tokens, latency, True
    except Exception:
        latency = time.time() - start
        return "", _estimate_tokens(system_prompt + user_prompt), 0, latency, False


def _estimate_tokens(text):
    return max(1, int(len(text.split()) * 1.3))
