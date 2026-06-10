"""
Configuration loader. All user settings live in config.toml at the project root.
Secrets (Telegram tokens, API keys, WG-Gesucht credentials) stay in .env.
"""
import os
import tomllib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def _load() -> dict:
    with open(ROOT_DIR / "config.toml", "rb") as f:
        return tomllib.load(f)


_cfg = _load()

# ─── Search ───────────────────────────────────────────────────────────────────
DEFAULT_MAX_RENT: int = _cfg["search"]["max_rent"]
MOVE_IN_FROM: str = _cfg["search"]["move_in_from"]
MOVE_IN_TO: str = _cfg["search"]["move_in_to"]
SEARCH_APARTMENTS: bool = _cfg["search"]["search_apartments"]
SEARCH_WG: bool = _cfg["search"]["search_wg"]
FURNISHED_ONLY: bool = _cfg["search"]["furnished_only"]
PETS_ALLOWED: bool = _cfg["search"]["pets_allowed"]
_apartment_cats: list[int] = _cfg["search"]["categories"]
SEARCH_CATEGORY_INDICES: list[int] = (
    ([0] if SEARCH_WG else []) + (_apartment_cats if SEARCH_APARTMENTS else [])
)
LAST_ONLINE_MAX_DAYS: int = _cfg["search"]["last_online_max_days"]
CRAWL_MAX_PAGES: int = _cfg["search"]["max_pages"]
HEADLESS: bool = _cfg["search"]["headless"]

# ─── Districts ────────────────────────────────────────────────────────────────
PREFERRED_DISTRICTS: list[str] = [d.lower() for d in _cfg["districts"]["preferred"]]
DISTRICT_FALLBACK_CITY: str = _cfg["districts"].get("fallback_city", "").lower()

# ─── WG filters ──────────────────────────────────────────────────────────────
WG_SIZE_MAX: int = _cfg["wg"]["wg_size_max"]
WG_FLATSHARE_TYPES: list[str] = _cfg["wg"]["flatshare_types"]

# ─── WG-Gesucht ───────────────────────────────────────────────────────────────
BASE_URL = "https://www.wg-gesucht.de"
SEARCH_URL: str = _cfg["search"]["url"]

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = Path(os.getenv("DATA_DIR", str(ROOT_DIR / "data")))
SEEN_IDS_FILE = DATA_DIR / "seen_ids.json"
SESSION_FILE = DATA_DIR / "session.json"

# ─── AI ───────────────────────────────────────────────────────────────────────
AI_ENABLED: bool = _cfg["ai"]["enabled"]
GEMINI_MODEL: str = _cfg["ai"]["model"]
AI_PROMPT_FILE = ROOT_DIR / "prompts" / "listing_analysis.md"
APPLICATION_DRAFT_PROMPT_FILE = ROOT_DIR / "prompts" / "application_draft.md"
APPLICATION_TEMPLATE_FILE = ROOT_DIR / "prompts" / "application_message.md"
MAX_AI_CALLS_PER_RUN: int = _cfg["ai"]["max_calls_per_run"]
MAX_DETAIL_CHARS: int = _cfg["ai"]["max_detail_chars"]
MAX_OUTPUT_TOKENS: int = _cfg["ai"]["max_output_tokens"]

# ─── Profile ──────────────────────────────────────────────────────────────────
PROFILE_NAME: str = _cfg["profile"]["name"]
PROFILE_CONTEXT: str = _cfg["profile"]["context"].strip()
PROFILE_MUST_HAVES: list[str] = _cfg["profile"]["must_haves"]
PROFILE_STRONG_PREFERENCES: list[str] = _cfg["profile"]["strong_preferences"]
PROFILE_NICE_TO_HAVES: list[str] = _cfg["profile"]["nice_to_haves"]
