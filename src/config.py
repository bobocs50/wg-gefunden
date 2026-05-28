"""
config.py — all user-tunable settings live here.

Edit this file to adjust your search preferences, date window, and budget.
Secrets (credentials, API keys) stay in .env — not here.
"""
from pathlib import Path

# ─── Search Preferences ───────────────────────────────────────────────────────
# A listing passes the district filter when its location string contains any of
# these values (case-insensitive match). Add or remove as needed.
PREFERRED_DISTRICTS: list[str] = [
    "eppendorf",
    "fuhlsbüttel",
    "fuhlsbuettel",
    "ohlsdorf",
    "alsterdorf",
    "barmbek-nord",
    "winterhude",
    "lokstedt",
    "langenhorn",
    "borgfelde",
]

# Fallback values used when the matching .env variable is not set.
# To override at runtime: set MAX_RENT / AVAILABLE_FROM / AVAILABLE_UNTIL in .env.
DEFAULT_MAX_RENT: int = 1500              # €/month ceiling
DEFAULT_AVAILABLE_FROM: str = "2026-08-15"   # ISO date — must be available by this date
DEFAULT_AVAILABLE_UNTIL: str = "2027-02-05"  # ISO date — must run at least until this date

# Listings whose landlord has been offline longer than this are filtered out.
LAST_ONLINE_MAX_DAYS: int = 7

# How many result pages to crawl per run (each page contains ~20 listings).
CRAWL_MAX_PAGES: int = 1

# Run Chromium in the background without opening a visible browser window.
HEADLESS: bool = True

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
SEEN_IDS_FILE = DATA_DIR / "seen_ids.json"
SESSION_FILE = DATA_DIR / "session.json"   # Playwright storage state (gitignored)

# ─── AI ───────────────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"
MAX_DETAIL_CHARS = 4000   # truncate scraped page content before sending to Gemini
MAX_OUTPUT_TOKENS = 1200  # cap Gemini response length

# ─── WG-Gesucht ───────────────────────────────────────────────────────────────
BASE_URL = "https://www.wg-gesucht.de"
# 1-room apartments + apartments + houses in Hamburg (WG-Gesucht category IDs 1, 2, 3)
SEARCH_URL = BASE_URL + "/1-zimmer-wohnungen-und-wohnungen-und-haeuser-in-Hamburg.55.1+2+3.1.0.html"
