

---

## Architecture / Technical Debt

- [x] **Move all user config to `config.toml`** — extract every user-editable setting (budget, dates, districts, categories, AI flags, renter profile) from `src/config.py` into a `config.toml` at the project root; make `src/config.py` a thin loader (`tomllib` is stdlib in 3.11+). `.env` keeps secrets only (tokens, API keys, credentials). This replaces the earlier "move renter profile" sub-item.
- [x] **Shared browser module** — extract `src/browser.py` with a single `authenticated_page()` context manager; eliminate the three independent Playwright setups in `auth.py`, `crawler.py`, and `scraper.py` that each duplicate session loading and cookie-banner dismissal
- [x] **Consolidate filter logic** — make `run_checks()` in `filters.py` the single source of truth; reduce `reject_reason()` to a one-liner that delegates to it (adding a filter currently requires editing both functions)
- [x] **Atomic seen-ID writes + early persistence** — write `seen_ids.json` immediately after crawl (not at the very end of main), and use a temp-file + `os.replace()` rename to prevent JSON corruption on mid-write crashes
- [x] **Surface Telegram send failures** — `send()` return value is currently ignored at all 4 call sites; log a warning and retry once so a Telegram outage is visible in logs rather than silently looking like zero matches
- [ ] **Fix district false negatives** — listings that show only `Hamburg | Ifflandstraße` (no sub-district) are rejected even if the detail page is in a preferred district; consider fetching the detail page to verify district before rejecting



# Roadmap

Checklist of missing features before this bot is usable by anyone, not just Hamburg-specific setups.

---

## 1. City configurability

> Currently hardcoded to Hamburg (`city_id=55`) in `SEARCH_URL` and the README.

- [ ] Add `CITY_NAME` and `CITY_ID` to `config.py` (user looks up their city once from the WG-Gesucht URL)
- [ ] Build `SEARCH_URL` dynamically from `CITY_NAME` + `CITY_ID` instead of hardcoding it
- [ ] Replace Hamburg-specific districts in `config.py` with commented examples that work for any city
- [ ] Update README to be city-agnostic (remove Hamburg references, explain how to find `CITY_ID`)

---

## 2. WG-Zimmer support

> Category 0 (WG-Zimmer / flatshare rooms) is excluded. When enabled, WG-specific filters are missing.

- [ ] Document that adding `0` to `SEARCH_CATEGORY_INDICES` enables WG-Zimmer search
- [ ] Add `WG_MIN_MEMBERS` / `WG_MAX_MEMBERS` — total number of people living in the flat
- [ ] Add `WG_GENDER` — `"any"` / `"female"` / `"male"` / `"mixed"`
- [ ] Add `WG_TYPES` — list from `["students", "professionals", "internationals", "seniors", "families"]` or `["any"]`
- [ ] Apply WG filters in `filters.py` (only active when category `0` is in `SEARCH_CATEGORY_INDICES`)
- [ ] Apply WG filters in the WG-Gesucht UI via `crawler.py` where possible (reduce server-side results)

---

## 3. Missing filter settings

> These filters are either hardcoded or not exposed at all.

- [ ] Add `MIN_RENT` — filter out suspiciously cheap listings (scam signal), env-var overridable
- [ ] Add `MIN_SIZE_M2` / `MAX_SIZE_M2` — apartment size in m² (currently not filtered at all)
- [ ] Add `FURNISHED_ONLY` boolean — hard filter, not just an AI preference
- [ ] Add `MOVE_IN_WINDOW_DAYS` — how many days after `AVAILABLE_FROM` a listing can still start (currently hardcoded to 30)
- [ ] Make `LAST_ONLINE_MAX_DAYS` overridable via env var (currently only in `config.py`)
- [ ] Add `RENT_TYPE` — `"warm"` / `"cold"` / `"both"` (currently hardcoded to both in `SEARCH_URL`)

---

## 4. Search / crawler settings

> Minor things hardcoded in the URL or crawler that limit flexibility.

- [ ] Add `SORT_BY` — `"date"` / `"price"` / `"relevance"` (currently always newest-first)
- [ ] Add `SORT_ORDER` — `"asc"` / `"desc"`
- [ ] Apply `RENT_TYPE`, `SORT_BY`, `SORT_ORDER` when building the dynamic search URL

---

## 5. Notification improvements

- [ ] **Score threshold gate** — add `MIN_RECOMMENDATION_SCORE` (0–10); only send AI-analysed listings that meet the threshold, others get a basic alert or are silently skipped
- [ ] **AI-drafted application message** — after a match, generate a personalised cover message and send it to Telegram with an Approve / Skip button before anything is sent to the landlord

---

## 6. Onboarding & usability

> Friction points for a new user setting this up from scratch.

- [ ] Add a `scripts/setup.py` that walks through config interactively and writes `.env`
- [ ] Add startup config validation — warn clearly if required fields (`TELEGRAM_BOT_TOKEN`, etc.) are missing instead of crashing mid-run
- [ ] Add a note in README / config explaining how to look up `CITY_ID` from a WG-Gesucht URL
- [ ] Add district examples for common German cities (Berlin, Munich, Frankfurt, Cologne) as commented-out blocks in `config.py`
