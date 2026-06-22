import json
import os
import threading

from openai import OpenAI

from src.config import (
    AI_PROMPT_FILE,
    APPLICATION_DRAFT_PROMPT_FILE,
    APPLICATION_TEMPLATE_FILE,
    OPENAI_MODEL,
    MAX_OUTPUT_TOKENS,
    PROFILE_CONTEXT,
    PROFILE_MUST_HAVES,
    PROFILE_NAME,
    PROFILE_NICE_TO_HAVES,
    PROFILE_STRONG_PREFERENCES,
)

_REQUIRED_KEYS = {"scam_score", "recommendation_score"}

_prompt_cache: str | None = None
_application_draft_cache: str | None = None
_application_template_cache: str | None = None
_client: OpenAI | None = None
_client_lock = threading.Lock()


def _load_prompt() -> str:
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = AI_PROMPT_FILE.read_text(encoding="utf-8")
    return _prompt_cache


def _load_application_draft() -> str:
    global _application_draft_cache
    if _application_draft_cache is None:
        _application_draft_cache = APPLICATION_DRAFT_PROMPT_FILE.read_text(encoding="utf-8")
    return _application_draft_cache


def _load_application_template() -> str:
    global _application_template_cache
    if _application_template_cache is None:
        _application_template_cache = APPLICATION_TEMPLATE_FILE.read_text(encoding="utf-8")
    return _application_template_cache


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


def _get_client() -> OpenAI:
    global _client
    with _client_lock:
        if _client is None:
            _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
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
    missing = _REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"Missing keys: {missing}")
    data["scam_score"] = max(1, min(10, int(data["scam_score"])))
    data["recommendation_score"] = max(1, min(10, int(data["recommendation_score"])))
    if not isinstance(data.get("pros"), list):
        data["pros"] = []
    if not isinstance(data.get("cons"), list):
        data["cons"] = []
    data.setdefault("summary", "")
    data.setdefault("scam_reason", "")
    if not isinstance(data.get("summary"), str):
        data["summary"] = ""
    return data


def analyze(listing: dict, detail_text: str) -> dict | None:
    """Call OpenAI to analyse a listing. Returns a validated result dict, or None on any failure."""
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set — skipping AI analysis")
        return None

    try:
        response = _get_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": _build_prompt(listing, detail_text)}],
            response_format={"type": "json_object"},
            max_tokens=MAX_OUTPUT_TOKENS,
        )
        data = json.loads(response.choices[0].message.content)
        return _validate(data)
    except Exception as e:
        print(f"OpenAI error: {e}")
        return None


def draft_application(listing: dict, detail_text: str) -> str | None:
    """Call OpenAI to fill in the application message template. Returns plain text, or None on failure."""
    if not os.getenv("OPENAI_API_KEY"):
        return None

    listing_block = (
        f"Title: {listing.get('title', '?')}\n"
        f"Price: {listing.get('price_text', '?')}\n"
        f"Location: {listing.get('location', '?')}\n"
        f"Dates: {listing.get('date_start', '?')} – {listing.get('date_end', '?')}"
    )
    detail_block = detail_text if detail_text else "(kein Detailtext verfügbar)"

    prompt = (
        _load_application_draft()
        .replace("{{APPLICATION_TEMPLATE}}", _load_application_template())
        .replace("{{LISTING}}", listing_block)
        .replace("{{DETAIL_TEXT}}", detail_block)
    )

    try:
        response = _get_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_OUTPUT_TOKENS,
        )
        text = response.choices[0].message.content.strip()
        return text if text else None
    except Exception as e:
        print(f"OpenAI application draft error: {e}")
        return None
