# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Python automation tool that crawls Hamburg rental listings (WG-Gesucht), filters them against hard criteria, runs optional AI analysis via Gemini, and sends Telegram push notifications for matches. Intended to run as a cron job every 10–15 minutes.

## Setup & Running

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env        # fill in credentials and API keys
python scripts/login.py     # one-time: opens browser, logs in, saves data/session.json
venv/bin/python3 main.py    # main entry point
```

There are no tests. Use `scripts/inspect_search.py` to interactively debug the browser automation.

## Configuration

- **`config.toml`**: all user-editable settings — budget, dates, districts, categories, AI flags, and renter profile. Edit this for normal customisation.
- **`.env`**: secrets only — Telegram tokens, API keys, WG-Gesucht credentials. See `.env.example`.
- **`src/config.py`**: thin loader; reads `config.toml` and exposes constants. Do not edit directly.
- **`prompts/listing_analysis.md`**: Gemini prompt template — `{{PROFILE}}`, `{{LISTING}}`, `{{DETAIL_TEXT}}` are injected at runtime.

Key `.env` vars:

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Push notifications |
| `GEMINI_API_KEY` | Required when `ai.enabled = true` in `config.toml` |
| `WGG_EMAIL` / `WGG_PASSWORD` | Used by `auth.py` auto-relogin and `scripts/login.py` |
| `DATA_DIR` | Override storage path (default: `./data`) |

## Architecture (`src/`)

| Module | Responsibility |
|---|---|
| `config.py` | Thin loader — reads `config.toml` using `tomllib` and exposes constants; paths and static URLs also live here |
| `auth.py` | `ensure_session()` — validates the saved session by loading WG-Gesucht headlessly and checking for the login button; auto-relogs if expired using `WGG_EMAIL`/`WGG_PASSWORD` |
| `crawler.py` | Playwright browser automation: loads session, applies UI filters (rent ceiling, date window, category) by clicking through the WG-Gesucht filter dropdowns, scrapes listing cards, paginates |
| `scraper.py` | `scrape_details(urls)` — visits individual listing detail pages and extracts description text (truncated to `MAX_DETAIL_CHARS`) for AI input |
| `filters.py` | Hard filters: type, price, district, date window, last-online recency. `run_checks()` returns per-filter results for console logging |
| `seen.py` | Reads/writes `data/seen_ids.json` — every scraped listing ID is persisted so re-runs skip already-processed listings |
| `telegram.py` | `send(text)`, `format_listing(listing)`, `format_listing_with_ai(listing, analysis)` |
| `ai.py` | `analyze(listing, detail_text)` — calls Gemini with a structured prompt, returns validated dict with `scam_score`, `recommendation_score`, `pros`, `cons`, `summary` |

## Data Flow

```
main.py
  └─ ensure_session()           # validate/refresh session
  └─ crawl()                    # browser automation → list of listing dicts
       └─ _apply_filters()      # click through WG-Gesucht filter UI
       └─ _scrape_page()        # parse listing cards per page
  └─ skip seen IDs
  └─ run_checks() per listing   # print ✓/✗ per filter
  └─ collect matches
  └─ if AI_ENABLED:
       └─ scrape_details()      # visit detail pages for AI input
       └─ analyze() × N         # Gemini calls (capped at MAX_AI_CALLS_PER_RUN)
       └─ send(format_listing_with_ai())
     else:
       └─ send(format_listing())
  └─ mark_seen()                # write all scraped IDs to disk
```

## Key Behaviours

- **Session reuse**: `data/session.json` is Playwright storage state, loaded on every run. `ensure_session()` validates it headlessly before crawling; if expired and credentials are set, it auto-relogs.
- **Seen ID dedup**: All listings per page are marked seen after each run regardless of whether they matched. A listing triggers a notification at most once.
- **UI filters**: Rent ceiling and date window are clicked through in the browser before scraping — they affect WG-Gesucht server-side results. Python filters are a second safety net.
- **Date window logic**: Listing must start by `DEFAULT_AVAILABLE_FROM + 30 days` (move-in window) and end at or after `DEFAULT_AVAILABLE_UNTIL`. Open-ended listings (no end date) pass if the start is on time.
- **District filter known limitation**: The filter checks the location string on the search result card. Listings that show only a generic `Hamburg` or a street name (e.g. `Hamburg | Ifflandstraße`) are rejected even if the detail page is in a preferred district.
- **AI cap**: The first `MAX_AI_CALLS_PER_RUN` matches get Gemini analysis; remaining matches get a basic Telegram alert without analysis.

## MVP Phases

- **v1** ✅ crawl + hard filter + Telegram alerts + AI analysis (Gemini)
- **v2** — score threshold gate (only notify if `recommendation_score ≥ N`)
- **v3** — AI-drafted application messages with Telegram approval button
