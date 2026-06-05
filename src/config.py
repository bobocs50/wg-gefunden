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
DEFAULT_AVAILABLE_FROM: str = _cfg["search"]["available_from"]
DEFAULT_AVAILABLE_UNTIL: str = _cfg["search"]["available_until"]
SEARCH_CATEGORY_INDICES: list[int] = _cfg["search"]["categories"]
LAST_ONLINE_MAX_DAYS: int = _cfg["search"]["last_online_max_days"]
CRAWL_MAX_PAGES: int = _cfg["search"]["max_pages"]
HEADLESS: bool = _cfg["search"]["headless"]

# ─── Districts ────────────────────────────────────────────────────────────────
PREFERRED_DISTRICTS: list[str] = [d.lower() for d in _cfg["districts"]["preferred"]]
DISTRICT_FALLBACK_CITY: str = _cfg["districts"].get("fallback_city", "").lower()

# ─── WG-Gesucht ───────────────────────────────────────────────────────────────
BASE_URL = "https://www.wg-gesucht.de"
SEARCH_URL = (
    BASE_URL
    + "/1-zimmer-wohnungen-und-wohnungen-und-haeuser-in-Hamburg.55.1+2+3.1.0.html"
    "?categories%5B%5D=1&categories%5B%5D=2&categories%5B%5D=3"
    "&rent_types%5B%5D=2&rent_types%5B%5D=1"
    "&rent_range=0%2C1000&min_rent=0&min_rent=1000"
    "&offer_filter=1&city_id=55&sort_column=1&sort_order=0&noDeact=1"
    "&dFr=1785578400&dTo=1801479600"
)

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = Path(os.getenv("DATA_DIR", str(ROOT_DIR / "data")))
SEEN_IDS_FILE = DATA_DIR / "seen_ids.json"
SESSION_FILE = DATA_DIR / "session.json"

# ─── AI ───────────────────────────────────────────────────────────────────────
AI_ENABLED: bool = _cfg["ai"]["enabled"]
GEMINI_MODEL: str = _cfg["ai"]["model"]
AI_PROMPT_FILE = ROOT_DIR / "prompts" / "listing_analysis.md"
MAX_AI_CALLS_PER_RUN: int = _cfg["ai"]["max_calls_per_run"]
MAX_DETAIL_CHARS: int = _cfg["ai"]["max_detail_chars"]
MAX_OUTPUT_TOKENS: int = _cfg["ai"]["max_output_tokens"]

# ─── Profile ──────────────────────────────────────────────────────────────────
PROFILE_NAME: str = _cfg["profile"]["name"]
PROFILE_CONTEXT: str = _cfg["profile"]["context"].strip()
PROFILE_MUST_HAVES: list[str] = _cfg["profile"]["must_haves"]
PROFILE_STRONG_PREFERENCES: list[str] = _cfg["profile"]["strong_preferences"]
PROFILE_NICE_TO_HAVES: list[str] = _cfg["profile"]["nice_to_haves"]
