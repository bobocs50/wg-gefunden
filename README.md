# WG-Gesucht Apartment Bot

> Watch Hamburg listings, filter out the noise, and get only the matches you care about.
> Gemini analysis is optional and disabled by default, so the bot stays cheap unless you turn it on.

## Quick Facts

| Item | Value |
|---|---|
| Language | Python |
| Crawler | Playwright |
| Alerts | Telegram |
| AI | Gemini, optional |
| Default crawl pages | `1` |
| Default AI calls per run | `3` |

## What It Does

| Step | Behavior |
|---|---|
| Crawl | Opens WG-Gesucht with Playwright and applies the search UI filters. |
| Filter | Checks rent, district, availability window, and landlord activity. |
| Deduplicate | Skips listings already saved in `data/seen_ids.json`. |
| Notify | Sends Telegram alerts for fresh matches. |
| Analyze | Optionally sends up to `MAX_AI_CALLS_PER_RUN` matches to Gemini. |

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Then fill in `.env` with your own values. Keep that file local.

## First Login

Run this once so the bot can reuse a saved WG-Gesucht session.

```bash
python scripts/login.py
```

This opens a browser, logs in, and saves `data/session.json`.

## Run

```bash
python main.py
```

Each run follows the same pipeline:

1. Loads your saved session.
2. Applies WG-Gesucht search filters in the browser.
3. Crawls `CRAWL_MAX_PAGES` pages.
4. Skips listings already stored in `data/seen_ids.json`.
5. Checks price, district, dates, and last-online recency.
6. Sends Telegram alerts for new matches.
7. Optionally sends up to `MAX_AI_CALLS_PER_RUN` matches to Gemini.

Example console flow:

```text
Session valid.
Filters applied — https://www.wg-gesucht.de/...
  page 1: 8 listings

  Helle Wohnung in Hamburg
    ✓ price      1000 €
    ✓ district   1-Zimmer-Wohnung | Hamburg | ...
    ✓ dates      01.08.2026 –
    ✓ online     unknown
    → MATCH
```

## Configuration

### `.env`

```env
# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# AI
AI_ENABLED=false
MAX_AI_CALLS_PER_RUN=3
MAX_DETAIL_CHARS=2500
MAX_OUTPUT_TOKENS=400
GEMINI_API_KEY=

# Crawl safety
CRAWL_MAX_PAGES=1

# Filters
MAX_RENT=1000
AVAILABLE_FROM=YYYY-MM-DD
AVAILABLE_UNTIL=YYYY-MM-DD

# WG-Gesucht login
WGG_EMAIL=
WGG_PASSWORD=
```

### Key Defaults

| Setting | Default | Why |
|---|---|---|
| `AI_ENABLED` | `false` | Zero Gemini usage until you opt in. |
| `MAX_AI_CALLS_PER_RUN` | `3` | Caps AI work per run. |
| `MAX_DETAIL_CHARS` | `2500` | Keeps the prompt compact. |
| `MAX_OUTPUT_TOKENS` | `400` | JSON summaries do not need more. |
| `CRAWL_MAX_PAGES` | `1` | Keeps cost and risk low. |

## What Gets Filtered

Before AI ever runs, a listing must pass these checks:

- Not already seen.
- Price at or below `MAX_RENT`.
- Location matches one of the preferred districts in `src/config.py`.
- Start and end dates fit your availability window.
- Landlord was online recently enough.

Only listings that pass all of that can reach Gemini.

## When AI Runs

AI is only used when all of these are true:

- `AI_ENABLED=true` in `.env`.
- `GEMINI_API_KEY` is set.
- The listing is new.
- The listing passes all local filters.
- The listing is within the first `MAX_AI_CALLS_PER_RUN` matches for that run.

If there are more matches than the cap, they still get basic Telegram alerts without AI analysis.

## Cost Controls

The defaults are intentionally conservative. Before deploying with AI enabled, set a billing budget and alert in Google Cloud or AI Studio.

## Deployment

### Local

- Use the setup steps above.
- Run `python scripts/login.py` once.
- Start with `python main.py`.

### Cloud

- Store `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `WGG_EMAIL`, and `WGG_PASSWORD` as secrets.
- Keep `AI_ENABLED=false` for the first deployment run.
- Keep `CRAWL_MAX_PAGES=1` unless you explicitly want more crawl load.
- Set a billing budget and alert before turning AI on.
- Do not log full listing text or prompt payloads.

## Safety

- Treat scraped listing text as untrusted.
- Do not paste real API keys into chat.
- Rotate any key that was exposed.
- Store secrets as environment variables or cloud secrets.
- Do not log full prompts, tokens, or scraped personal data.

## Troubleshooting

- If the browser fails to start, reinstall Chromium with `playwright install chromium`.
- If `main.py` exits before crawling, run `python scripts/login.py` again to refresh the session.
- If AI never runs, check `AI_ENABLED=true` and `GEMINI_API_KEY` in `.env`.
- If matches look wrong, edit the filters in `src/config.py`.

## Repository Map

```text
main.py                       Main run loop
src/config.py                 Search, AI, and safety settings
src/crawler.py                Playwright crawler and search filters
src/filters.py                Local hard filters
src/scraper.py                Detail-page text scraping for AI
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
