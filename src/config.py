"""
User preferences for the apartment search.

Edit this file for normal customization. Keep secrets such as API keys,
Telegram tokens, and WG-Gesucht login credentials in .env.
"""
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int, minimum: int | None = None) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    if minimum is not None:
        return max(minimum, parsed)
    return parsed

# ─── Search Preferences ───────────────────────────────────────────────────────
# A listing passes the district filter when its location string contains any of
# these values (case-insensitive match). Add or remove districts as needed.
PREFERRED_DISTRICTS: list[str] = [
    "eppendorf",
    "fuhlsbuettel",
    "fuhlsbüttel",
    "ohlsdorf",
    "alsterdorf",
    "barmbek-nord",
    "winterhude",
    "lokstedt",
    "langenhorn",
    "borgfelde",
]

DEFAULT_MAX_RENT: int = _int_env("MAX_RENT", 1500, minimum=1)
DEFAULT_AVAILABLE_FROM: str = os.getenv("AVAILABLE_FROM", "2026-08-15")
DEFAULT_AVAILABLE_UNTIL: str = os.getenv("AVAILABLE_UNTIL", "2027-02-05")

# Listings whose landlord has been offline longer than this are filtered out.
LAST_ONLINE_MAX_DAYS: int = 7

# How many result pages to crawl per run. Each page contains roughly 20 listings.
CRAWL_MAX_PAGES: int = _int_env("CRAWL_MAX_PAGES", 1, minimum=1)

# Run Chromium in the background without opening a visible browser window.
HEADLESS: bool = _bool_env("HEADLESS", True)

# ─── WG-Gesucht ───────────────────────────────────────────────────────────────
BASE_URL = "https://www.wg-gesucht.de"
SEARCH_URL = BASE_URL + "/1-zimmer-wohnungen-und-wohnungen-und-haeuser-in-Hamburg.55.1+2+3.1.0.html"

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = ROOT_DIR / "data"
SEEN_IDS_FILE = DATA_DIR / "seen_ids.json"
SESSION_FILE = DATA_DIR / "session.json"

# ─── AI ───────────────────────────────────────────────────────────────────────
AI_ENABLED: bool = _bool_env("AI_ENABLED", False)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
AI_PROMPT_FILE = ROOT_DIR / "prompts" / "listing_analysis.md"

# Per run: scrape and summarize at most this many matching listings with AI.
# Extra matches still get basic Telegram alerts.
MAX_AI_CALLS_PER_RUN: int = _int_env("MAX_AI_CALLS_PER_RUN", 3, minimum=0)
MAX_DETAIL_CHARS: int = _int_env("MAX_DETAIL_CHARS", 2500, minimum=0)
MAX_OUTPUT_TOKENS: int = _int_env("MAX_OUTPUT_TOKENS", 400, minimum=1)

# This profile is inserted into prompts/listing_analysis.md at {{PROFILE}}.
PROFILE_NAME = "Apartment seeker"
PROFILE_CONTEXT = (
    "Starting a 5-month internship at Lufthansa Technik Hamburg in September 2026. "
    "Lufthansa Technik is near Hamburg Airport/Fuhlsbuettel, so commute time matters. "
    "Needs a sublet from August 2026 through the end of January 2027."
)
PROFILE_MUST_HAVES: list[str] = [
    "Furnished, because they do not own furniture",
    "Sublet is allowed",
    "Available for the requested date window",
]
PROFILE_STRONG_PREFERENCES: list[str] = [
    "Quiet neighbourhood",
    "Short commute to Fuhlsbuettel",
    "Good public transport",
]
PROFILE_NICE_TO_HAVES: list[str] = [
    "Natural light",
    "Balcony",
    "Washing machine",
    "Fast internet",
    "Friendly flatmates",
]
