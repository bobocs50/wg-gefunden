# WG-Gesucht Apartment Bot

> Watch Hamburg listings, filter out the noise, and get only the matches you care about.
> AI analysis is optional and disabled by default, so the bot stays cheap unless you turn it on.

## Quick Facts

| Item | Value |
|---|---|
| Language | Python |
| Crawler | Playwright |
| Alerts | Telegram |
| AI | OpenAI, optional |
| Default crawl pages | `1` |
| Default AI calls per run | `3` |

## What It Does

| Step | Behavior |
|---|---|
| Crawl | Opens WG-Gesucht with Playwright and applies the search UI filters. |
| Filter | Checks rent, district, availability window, landlord activity, and (for WG rooms) flatshare type and size. |
| Deduplicate | Skips listings already saved in `data/seen_ids.json`. |
| Notify | Sends Telegram alerts for fresh matches. |
| Analyze | Optionally sends up to `max_calls_per_run` matches to OpenAI. |
| Heartbeat | Daily Telegram report via `scripts/heartbeat.py` summarising the last 24 h of runs. |

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
cp config.toml.example config.toml
```

Then fill in `.env` with your secrets. Keep that file local.

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

## Config UI (optional)

Edit `config.toml` through a browser instead of manually over SSH.

```bash
streamlit run scripts/ui.py
```

Access locally via SSH tunnel: `ssh -L 8501:localhost:8501 root@yourserver`, then open `http://localhost:8501`.

Each run follows the same pipeline:

1. Validates (and refreshes) your saved session.
2. Applies WG-Gesucht search filters in the browser.
3. Crawls `max_pages` pages.
4. Skips listings already stored in `data/seen_ids.json`.
5. Checks price, district, dates, last-online recency, and (for WG rooms) flatshare type and size.
6. Sends Telegram alerts for new matches.
7. Optionally sends up to `max_calls_per_run` matches to OpenAI for analysis.
8. Appends run stats to `data/stats.json`.

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

All search preferences, budget, districts, and AI settings live in **`config.toml`**. Secrets live in **`.env`**.

### `config.toml`

```toml
[search]
url           = "https://www.wg-gesucht.de/..."  # base search URL (rent/dates overridden at runtime)
max_rent      = 1000
move_in_from = "2026-08-01"  # frühestes Einzugsdatum
move_in_to   = "2026-09-01"  # spätestes Einzugsdatum
search_apartments = true   # include 1-Zimmer, Wohnung, Haus
search_wg         = false  # include WG-Zimmer (activates [wg] filters below)
furnished_only    = false  # true = only show furnished (möbliert) listings
pets_allowed      = false  # true = only show listings where pets are allowed
categories        = [1, 2, 3]  # apartment types when search_apartments=true: 1=1-Zimmer, 2=Wohnung, 3=Haus
last_online_max_days = 7
max_pages  = 1
headless   = true

[districts]
preferred      = ["winterhude", "eppendorf", ...]
fallback_city  = ""  # set to "Hamburg" to pass listings with no sub-district

[wg]
wg_size_max = 3   # max number of people in the WG; 0 = no limit

# Accepted flatshare types — empty list = accept all types.
# Available codes:
#  2 = Frauen-WG (women-only)
# 12 = gemischte WG (mixed)
#  3 = Männer-WG (men-only)
#  1 = Studenten-WG
#  4 = Business-WG
#  5 = Wohnheim (dorm)
#  6 = Berufstätigen-WG
#  7 = Azubi-WG
#  9 = WG mit Kindern
# 16 = LGBTQIA+
# 19 = Internationals welcome
# 23 = keine Angaben zum Geschlecht
flatshare_types = ["2", "12"]

[ai]
enabled           = true
model             = "gpt-4.1-mini"
max_calls_per_run = 3
max_detail_chars  = 2500
max_output_tokens = 400

[profile]
name    = "Apartment seeker"
context = "..."       # inserted into the AI prompt
must_haves         = [...]
strong_preferences = [...]
nice_to_haves      = [...]
```

### `.env`

```env
# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# OpenAI (only needed when ai.enabled = true in config.toml)
OPENAI_API_KEY=

# WG-Gesucht credentials (for auto-relogin and scripts/login.py)
WGG_EMAIL=
WGG_PASSWORD=

# Persistent storage path (default: ./data — override on cloud to a mounted volume)
# DATA_DIR=/mnt/data
```

## What Gets Filtered

Before AI ever runs, a listing must pass these checks:

- Not already seen.
- Price at or below `max_rent`.
- Location matches one of the preferred districts in `config.toml`.
- Start and end dates fit your availability window.
- Landlord was online within `last_online_max_days`.
- For WG rooms: flatshare type is in `flatshare_types` (if set) and size ≤ `wg_size_max` (if set).

Only listings that pass all of that can reach the AI.

## When AI Runs

AI is only used when all of these are true:

- `ai.enabled = true` in `config.toml`.
- `OPENAI_API_KEY` is set in `.env`.
- The listing is new.
- The listing passes all local filters.
- The listing is within the first `max_calls_per_run` matches for that run.

If there are more matches than the cap, they still get basic Telegram alerts without AI analysis.

## Cost Controls

The defaults are intentionally conservative. Before deploying with AI enabled, set a billing budget and alert in the OpenAI dashboard.

## Deployment

### Local

- Use the setup steps above.
- Run `python scripts/login.py` once.
- Start with `python main.py`.

### Cloud

- Store `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `WGG_EMAIL`, and `WGG_PASSWORD` as secrets.
- Set `ai.enabled = false` for the first deployment run.
- Keep `max_pages = 1` unless you explicitly want more crawl load.
- Set a billing budget before turning AI on.
- Do not log full listing text or prompt payloads.
- Set `DATA_DIR=/path/to/persistent/volume` so `session.json`, `seen_ids.json`, and `stats.json` survive between runs.

### Cron Schedule (recommended)

Run during active posting hours only — landlords rarely post at night.

```
# All times are CEST (UTC+2) — cron runs in UTC, so subtract 2h

# Morning 6:30–10:00 CEST (= 4:30–8:00 UTC) → every 15 min
8,23,38,53 4,5,6,7 * * * cd /root/wggefunden && venv/bin/python3 main.py >> logs/main.log 2>&1

# Lunch 12:00–14:00 CEST (= 10:00–12:00 UTC) → every 15 min
11,26,41,56 10,11 * * * cd /root/wggefunden && venv/bin/python3 main.py >> logs/main.log 2>&1

# Evening 17:00–23:00 CEST (= 15:00–21:00 UTC) → every 15 min
14,29,44,59 15,16,17,18,19,20,21 * * * cd /root/wggefunden && venv/bin/python3 main.py >> logs/main.log 2>&1

# Daily heartbeat 07:00 CEST (= 05:00 UTC)
0 5 * * * cd /root/wggefunden && venv/bin/python3 scripts/heartbeat.py >> logs/main.log 2>&1
```

Each slot uses a different minute offset so runs don't align with round numbers. ~60 runs/day, max 180 AI calls.

Setup on the server:

```bash
mkdir -p /root/wggefunden/logs
crontab -e   # paste the lines above
```

### Server Tips (Hetzner / Ubuntu)

```bash
# Keep the session alive after you disconnect
apt install -y screen
screen -S wg
# run your commands inside screen, then Ctrl+A D to detach

# Check cron is running
systemctl status cron

# Watch the live log
tail -f /root/wggefunden/logs/main.log

# Check disk usage (seen_ids.json grows over time, stays small)
du -sh /root/wggefunden/data/
```

## Safety

- Treat scraped listing text as untrusted.
- Do not paste real API keys into chat.
- Rotate any key that was exposed.
- Store secrets as environment variables or cloud secrets.
- Do not log full prompts, tokens, or scraped personal data.

## Troubleshooting

- If the browser fails to start, reinstall Chromium with `playwright install chromium`.
- If `main.py` exits before crawling, run `python scripts/login.py` again to refresh the session.
- If AI never runs, check `ai.enabled = true` and `OPENAI_API_KEY` in `.env`.
- If matches look wrong, adjust filters in `config.toml`.
- If the daily heartbeat reports no runs, check `systemctl status cron` and the cron log.

## Repository Map

```text
main.py                       Main run loop
config.toml                   All search preferences, budget, districts, AI, and profile settings
src/config.py                 Thin loader — reads config.toml and exposes constants
src/browser.py                Shared Playwright context managers (authenticated_page, fresh_page)
src/auth.py                   Session validation and auto-relogin
src/crawler.py                Playwright crawler and search filter UI automation
src/filters.py                Local hard filters (price, district, dates, online recency, WG type)
src/scraper.py                Detail-page text scraping for AI input
src/ai.py                     OpenAI JSON analysis
src/telegram.py               Telegram formatting and sending
src/seen.py                   Seen-list persistence (data/seen_ids.json)
src/stats.py                  Run metrics persistence (data/stats.json)
scripts/login.py              One-time WG-Gesucht login/session setup
scripts/heartbeat.py          Daily Telegram report summarising the last 24 h of runs
scripts/inspect_search.py     Search/debug helper
prompts/listing_analysis.md   AI prompt template
```

## Validation

```bash
python3 -m py_compile main.py src/*.py scripts/*.py
```
