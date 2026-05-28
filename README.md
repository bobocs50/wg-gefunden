# WG-Gesucht Apartment Bot

Python bot for crawling WG-Gesucht listings in Hamburg, filtering apartments against your criteria, and sending Telegram alerts. Optional Gemini analysis can score matching listings, but AI is disabled by default to avoid unexpected cost.

## What It Does

- Opens WG-Gesucht with Playwright.
- Applies server-side search filters for rent and availability dates.
- Scrapes one result page by default.
- Skips listings already stored in `data/seen_ids.json`.
- Runs local filters for price, district, dates, and landlord activity.
- Sends Telegram alerts for new matches.
- Optionally analyzes up to `MAX_AI_CALLS_PER_RUN` matches with Gemini.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Edit `.env` and fill in your own credentials. Do not commit `.env`.

## Environment Variables

```env
# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# AI safety
AI_ENABLED=false
MAX_AI_CALLS_PER_RUN=3
MAX_DETAIL_CHARS=2500
MAX_OUTPUT_TOKENS=400
GEMINI_API_KEY=

# Crawl safety
CRAWL_MAX_PAGES=1

# Filters
MAX_RENT=1000
AVAILABLE_FROM=2026-12-15
AVAILABLE_UNTIL=2027-02-01

# WG-Gesucht credentials
WGG_EMAIL=
WGG_PASSWORD=
```

## First Login

Run this once to create `data/session.json`:

```bash
python scripts/login.py
```

This opens a browser, logs into WG-Gesucht, and saves the session for future runs.

## Run

```bash
python main.py
```

The bot prints every scraped listing, including whether it was skipped because it was already seen or rejected by a filter.

## When AI Runs

AI only runs when all of these are true:

1. `AI_ENABLED=true` in `.env`.
2. `GEMINI_API_KEY` is set.
3. The listing is not already in `data/seen_ids.json`.
4. The listing passes all local filters.
5. The listing is within the first `MAX_AI_CALLS_PER_RUN` matches for that run.

With the default `AI_ENABLED=false`, Gemini token usage is zero.

## Filters Before AI

The bot filters before any AI call:

- Already-seen listing ID.
- Price under `MAX_RENT`.
- District is in `PREFERRED_DISTRICTS` in `src/config.py`.
- Availability fits `AVAILABLE_FROM` and `AVAILABLE_UNTIL`.
- Landlord last-online date is recent enough.

Only listings that pass these checks can reach Gemini.

## Cost Controls

Defaults are intentionally conservative:

- `AI_ENABLED=false`
- `MAX_AI_CALLS_PER_RUN=3`
- `MAX_DETAIL_CHARS=2500`
- `MAX_OUTPUT_TOKENS=400`
- `CRAWL_MAX_PAGES=1`

Before deploying with AI enabled, set a Google Cloud or AI Studio billing budget and alert. Keep AI off during initial deployment tests.

## Security Notes

- Treat scraped listing text as untrusted.
- Never paste or commit real API keys.
- Rotate any key that was shared in chat or committed by mistake.
- Store deployment secrets as cloud secrets or environment variables.
- Do not log full prompts, credentials, API keys, or scraped personal data.

## Project Structure

```text
main.py                       Main run loop
src/config.py                 Search, AI, and safety settings
src/crawler.py                Playwright WG-Gesucht crawler
src/filters.py                Local hard filters
src/scraper.py                Detail-page text scraper for AI
src/ai.py                     Gemini JSON analysis
src/telegram.py               Telegram formatting and sending
src/seen.py                   Seen-list persistence
scripts/login.py              One-time WG-Gesucht login/session setup
scripts/inspect_search.py     Search/debug helper
prompts/listing_analysis.md   Gemini prompt template
notes/cloud_safety.md         Deployment safety checklist
```

## Validation

```bash
python3 -m py_compile main.py src/*.py scripts/*.py
```

