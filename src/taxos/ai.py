"""Clasificación opcional por IA (solo nombres de archivo)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"


def get_api_key() -> str | None:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    return key or None


def suggest_categories(
    names: list[str],
    categories: list[str],
    api_key: str,
    *,
    timeout: float = 30.0,
) -> dict[str, str]:
    """Pide a Groq una categoría por nombre. Devuelve {} si falla."""
    if not names or not api_key:
        return {}

    allowed = sorted(set(categories) | {"other"})
    payload_names = names[:100]
    system = (
        "Clasifica archivos solo por su nombre. "
        "Responde ÚNICAMENTE un JSON objeto {\"nombre.ext\": \"categoria\"}. "
        f"Categorías permitidas: {', '.join(allowed)}. "
        "Si no estás seguro usa other. No inventes categorías."
    )
    user = "Archivos:\n" + "\n".join(f"- {n}" for n in payload_names)

    try:
        response = httpx.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        content = data["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError):
        return {}

    parsed = _parse_json_object(content)
    if not parsed:
        return {}

    allowed_set = set(allowed)
    result: dict[str, str] = {}
    for name, category in parsed.items():
        if not isinstance(name, str) or not isinstance(category, str):
            continue
        cat = category.strip().lower()
        if cat in allowed_set:
            result[name] = cat
    return result


def _parse_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None
