"""One LLM call per @agent message. Failures return a clear string, never crash the room."""

import os
from typing import List, Dict, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()

TIMEOUT_SECONDS = 25.0


def _pick_provider() -> str:
    if LLM_PROVIDER in ("groq", "openai", "gemini"):
        return LLM_PROVIDER
    if GROQ_API_KEY:
        return "groq"
    if OPENAI_API_KEY:
        return "openai"
    if GEMINI_API_KEY:
        return "gemini"
    return "mock"


def build_prompt(user_name: str, history: List[Dict], question: str) -> List[Dict[str, str]]:
    """
    Only THIS user's history goes into the prompt.
    That is the whole point of context isolation.
    """
    system = (
        f"You are @agent, a helpful teammate in a shared chat room. "
        f"You are answering {user_name} only. "
        f"Use only the conversation context provided for this user. "
        f"Be concise and practical. If context is thin, say what you need."
    )
    messages = [{"role": "system", "content": system}]

    for item in history[-12:]:
        role = item.get("role", "user")
        content = item.get("content", "")
        if role == "agent":
            messages.append({"role": "assistant", "content": content})
        else:
            messages.append({"role": "user", "content": content})

    messages.append({"role": "user", "content": question})
    return messages


async def call_llm(user_name: str, history: List[Dict], question: str) -> str:
    provider = _pick_provider()
    messages = build_prompt(user_name, history, question)

    try:
        if provider == "groq":
            return await _call_openai_compatible(
                "https://api.groq.com/openai/v1/chat/completions",
                GROQ_API_KEY,
                "openai/gpt-oss-20b",
                messages,
            )
        if provider == "openai":
            return await _call_openai_compatible(
                "https://api.openai.com/v1/chat/completions",
                OPENAI_API_KEY,
                "gpt-4o-mini",
                messages,
            )
        if provider == "gemini":
            return await _call_gemini(messages)
        return (
            f"[mock agent] Hi {user_name}. I got: \"{question}\". "
            f"Add GROQ_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY in backend/.env for real answers."
        )
    except httpx.TimeoutException:
        return (
            f"Sorry {user_name}, the model timed out. "
            f"Your question was saved — try again in a moment."
        )
    except Exception as exc:
        return (
            f"Sorry {user_name}, I hit an error talking to the model "
            f"({type(exc).__name__}). The room is still fine — please retry."
        )


async def _call_openai_compatible(
    url: str, api_key: str, model: str, messages: List[Dict[str, str]]
) -> str:
    if not api_key:
        raise RuntimeError("Missing API key")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 400,
    }
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"LLM HTTP {resp.status_code}: {resp.text[:180]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


async def _call_gemini(messages: List[Dict[str, str]]) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("Missing Gemini API key")
    # Flatten chat into a single prompt for simplicity
    parts = []
    for m in messages:
        parts.append(f"{m['role'].upper()}: {m['content']}")
    text = "\n".join(parts)
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {"contents": [{"parts": [{"text": text}]}]}
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
