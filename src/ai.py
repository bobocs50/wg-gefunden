import json
import os
import threading

from google import genai
from google.genai import types

from src.config import (
    AI_PROMPT_FILE,
    GEMINI_MODEL,
    MAX_OUTPUT_TOKENS,
    PROFILE_CONTEXT,
    PROFILE_MUST_HAVES,
    PROFILE_NAME,
    PROFILE_NICE_TO_HAVES,
    PROFILE_STRONG_PREFERENCES,
)

_REQUIRED_KEYS = {"scam_score", "scam_reason", "recommendation_score", "pros", "cons", "summary"}

_prompt_cache: str | None = None
_client: genai.Client | None = None
_client_lock = threading.Lock()


def _load_prompt() -> str:
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = AI_PROMPT_FILE.read_text(encoding="utf-8")
    return _prompt_cache


def _bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- Not specified"


def _profile_block() -> str:
    return "\n".join(
        [
            f"Name: {PROFILE_NAME}",
            "",
            "Context:",
            PROFILE_CONTEXT or "Not specified",
            "",
            "Must-haves:",
            _bullet_list(PROFILE_MUST_HAVES),
            "",
            "Strong preferences:",
            _bullet_list(PROFILE_STRONG_PREFERENCES),
            "",
            "Nice to have:",
            _bullet_list(PROFILE_NICE_TO_HAVES),
        ]
    )


def _get_client() -> genai.Client:
    global _client
    with _client_lock:
        if _client is None:
            _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _build_prompt(listing: dict, detail_text: str) -> str:
    listing_block = (
        f"Title: {listing.get('title', '?')}\n"
        f"Price: {listing.get('price_text', '?')}\n"
        f"Location: {listing.get('location', '?')}\n"
        f"Dates: {listing.get('date_start', '?')} – {listing.get('date_end', '?')}\n"
        f"URL: {listing.get('url', '?')}"
    )
    detail_block = detail_text if detail_text else "(no detail text available)"

    return (
        _load_prompt()
        .replace("{{PROFILE}}", _profile_block())
        .replace("{{LISTING}}", listing_block)
        .replace("{{DETAIL_TEXT}}", detail_block)
    )


def _validate(data: dict) -> dict:
    if not _REQUIRED_KEYS.issubset(data.keys()):
        raise ValueError(f"Missing keys: {_REQUIRED_KEYS - data.keys()}")
    data["scam_score"] = max(1, min(10, int(data["scam_score"])))
    data["recommendation_score"] = max(1, min(10, int(data["recommendation_score"])))
    if not isinstance(data["pros"], list):
        data["pros"] = []
    if not isinstance(data["cons"], list):
        data["cons"] = []
    return data


def analyze(listing: dict, detail_text: str) -> dict | None:
    """Call Gemini to analyse a listing. Returns a validated result dict, or None on any failure."""
    if not os.getenv("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY not set — skipping AI analysis")
        return None

    try:
        response = _get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=_build_prompt(listing, detail_text),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=MAX_OUTPUT_TOKENS,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        data = json.loads(response.text)
        return _validate(data)
    except Exception as e:
        print(f"Gemini error: {e}")
        return None
