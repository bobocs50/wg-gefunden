# Roadmap

## Setup

- [x] Init Python project (`requirements.txt`)
- [x] Configure `.env` (API keys, Telegram token, budget, filters)
- [x] Install dependencies (`pip install -r requirements.txt`)
- [x] Install Playwright Chromium (`playwright install chromium`)
- [x] Set up Telegram bot via BotFather

---

## v1 – Crawl + Filter + Alert

### Login
- [x] Run `login.py` — opens browser, logs into WG-Gesucht, saves `session.json`
- [x] Verify session saved to `data/session.json`

### WG-Gesucht Crawler
- [x] Load session on each run (skip login if valid)
- [x] Scrape listing cards from search results page
- [x] Extract: title, price, district, dates, URL, listing ID
- [x] Paginate through results

### Seen ID Tracking
- [x] Read `seen_ids.json` on startup
- [x] Skip already-seen listings
- [x] Write new IDs after processing

### Filters
- [x] Price ≤ budget
- [x] Rental period overlaps Aug–Feb
- [x] District matches preferred list
- [ ] Fix district false negatives: current filter only checks district strings in the search result card location. Listings that show only generic `Hamburg` or a street, e.g. `Hamburg | Ifflandstraße`, are rejected even if the detail page might be in a preferred district.

### Telegram Notifications
- [x] Send basic alert (title, price, district, URL)
- [x] Test end-to-end: crawl → filter → message received

### Scheduling
- [x] Set up cron job (every 15 min)
- [x] Test unattended runs

---

## v2 – AI Layer

- [x] Integrate Gemini SDK
- [x] Write evaluation prompt (score, scam check, pros/cons)
- [x] Parse AI response reliably
- [x] Add AI score + summary to Telegram message
- [x] Scam warning if detected
- [ ] Only notify if score ≥ threshold (configurable)

---

## v3 – Application Drafts

- [ ] AI generates personalized application message per listing
- [ ] Draft stored locally for review
- [ ] Telegram message includes "approve to send" button
- [ ] On approval: send message to landlord (semi-automatic)

---

## Deployment – Hetzner VPS

- [x] Rent Hetzner CX22 (~€3.79/mo)
- [x] SSH in, install Python + Playwright + Chromium
- [x] Upload code + `.env`
- [x] Run `login.py` on server to generate session
- [x] Set up cron job on server
- [x] Monitor logs

---

## Architecture / Technical Debt

- [ ] **Shared browser module** — extract `src/browser.py` with a single `authenticated_page()` context manager; eliminate the three independent Playwright setups in `auth.py`, `crawler.py`, and `scraper.py` that each duplicate session loading and cookie-banner dismissal
- [ ] **Consolidate filter logic** — make `run_checks()` in `filters.py` the single source of truth; reduce `reject_reason()` to a one-liner that delegates to it (adding a filter currently requires editing both functions)
- [ ] **Move renter profile out of config** — `PROFILE_*` constants in `config.py` belong to the AI layer; move them to `profiles/default.toml` so the profile can be swapped without touching search preferences
- [ ] **Atomic seen-ID writes + early persistence** — write `seen_ids.json` immediately after crawl (not at the very end of main), and use a temp-file + `os.replace()` rename to prevent JSON corruption on mid-write crashes
- [ ] **Surface Telegram send failures** — `send()` return value is currently ignored at all 4 call sites; log a warning and retry once so a Telegram outage is visible in logs rather than silently looking like zero matches
- [ ] **Fix district false negatives** — listings that show only `Hamburg | Ifflandstraße` (no sub-district) are rejected even if the detail page is in a preferred district; consider fetching the detail page to verify district before rejecting
