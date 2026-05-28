# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Python automation tool that crawls Hamburg rental listings (WG-Gesucht), filters them against hard criteria, and sends Telegram push notifications for matches. Intended to run as a cron job every 10–15 minutes.

## Setup & Running

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env        # fill in credentials and preferences
python scripts/login.py     # one-time: opens browser, logs in, saves data/session.json
venv/bin/python3 main.py    # main entry point
```

## Configuration

All tunable settings (districts, budget defaults, date window, page count) live in **`src/config.py`** — edit there, not in `.env`. Secrets go in `.env`:

| Variable | Purpose |
|---|---|
| `MAX_RENT` | Overrides `DEFAULT_MAX_RENT` in config.py |
| `AVAILABLE_FROM` / `AVAILABLE_UNTIL` | ISO dates — overrides defaults in config.py |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Push notifications (not yet wired into main) |
| `GEMINI_API_KEY` | AI summaries (v2, not yet implemented) |
| `WGG_EMAIL` / `WGG_PASSWORD` | Used only by `scripts/login.py` |

## Architecture (`src/`)

| Module | Responsibility |
|---|---|
| `config.py` | Single source of truth for all settings, paths, and constants |
| `crawler.py` | Playwright browser automation: loads session, applies UI filters (rent, dates, category), scrapes listing cards, paginates |
| `filters.py` | Hard filters run in Python: price, district, date window, last-online recency. `run_checks()` returns per-filter results for console logging; `reject_reason()` returns the first failing filter |
| `seen.py` | Reads/writes `data/seen_ids.json` — every scraped listing ID is persisted so re-runs skip already-processed listings |
| `telegram.py` | `send(text)` and `format_listing(listing)` — exists but not yet called from `main.py` |

## Data Flow

`main.py` → `crawl()` returns list of listing dicts → skip seen IDs → `run_checks()` per listing → print ✓/✗ per filter → collect matches → print summary → `mark_seen()` writes all scraped IDs to disk.

## Key Behaviours

- **Session reuse**: `data/session.json` is loaded on every run (Playwright storage state). If missing, crawls without login.
- **Seen ID dedup**: All 25 listings per page are marked seen after each run, regardless of whether they matched. A listing triggers a notification at most once.
- **UI filters applied on every run**: rent ceiling and date window are clicked through in the browser before scraping — they affect what WG-Gesucht returns server-side. Python filters are a second safety net.
- **Date window logic**: listing must start by `AVAILABLE_FROM + 30 days` (move-in window) and end at or after `AVAILABLE_UNTIL`. Open-ended listings (no end date) pass if the start is on time.
- **`CRAWL_MAX_PAGES`** in config.py controls pagination (default 3 = ~75 listings).

## MVP Phases

- **v1** ✅ crawl + hard filter + console output (Telegram code exists, not yet wired)
- **v2** — Gemini summary + scam score + score threshold gate
- **v3** — AI-drafted application messages with Telegram approval button
