

---

## Architecture / Technical Debt

- [x] **Move all user config to `config.toml`** — extract every user-editable setting (budget, dates, districts, categories, AI flags, renter profile) from `src/config.py` into a `config.toml` at the project root; make `src/config.py` a thin loader (`tomllib` is stdlib in 3.11+). `.env` keeps secrets only (tokens, API keys, credentials). This replaces the earlier "move renter profile" sub-item.
- [x] **Shared browser module** — extract `src/browser.py` with a single `authenticated_page()` context manager; eliminate the three independent Playwright setups in `auth.py`, `crawler.py`, and `scraper.py` that each duplicate session loading and cookie-banner dismissal
- [x] **Consolidate filter logic** — make `run_checks()` in `filters.py` the single source of truth; reduce `reject_reason()` to a one-liner that delegates to it (adding a filter currently requires editing both functions)
- [x] **Atomic seen-ID writes + early persistence** — write `seen_ids.json` immediately after crawl (not at the very end of main), and use a temp-file + `os.replace()` rename to prevent JSON corruption on mid-write crashes
- [x] **Surface Telegram send failures** — `send()` return value is currently ignored at all 4 call sites; log a warning and retry once so a Telegram outage is visible in logs rather than silently looking like zero matches


---

## 2. WG-Zimmer support

> Category 0 (WG-Zimmer / flatshare rooms) is excluded. When enabled, WG-specific filters are missing.

- [x] Document that adding `0` to `SEARCH_CATEGORY_INDICES` enables WG-Zimmer search — replaced by `search_wg` toggle in `config.toml`
- [x] Add `WG_MIN_MEMBERS` / `WG_MAX_MEMBERS` — implemented as `wg_size_max` in `config.toml [wg]`
- [x] Add `WG_GENDER` — implemented as `flatshare_types` (WG-Gesucht type codes) in `config.toml [wg]`
- [x] Add `WG_TYPES` — covered by `flatshare_types` (same type code list)
- [x] Apply WG filters in `filters.py` (only active when category `0` is in `SEARCH_CATEGORY_INDICES`)
- [x] Apply WG filters in the WG-Gesucht UI via `crawler.py` where possible (reduce server-side results)

---

## 3. Missing filter settings

> These filters are either hardcoded or not exposed at all.

- [ ] Add `MIN_RENT` — filter out suspiciously cheap listings (scam signal), env-var overridable
- [ ] Add `MIN_SIZE_M2` / `MAX_SIZE_M2` — apartment size in m² (currently not filtered at all)
- [ ] Add `FURNISHED_ONLY` boolean — hard filter, not just an AI preference
- [ ] Add `MOVE_IN_WINDOW_DAYS` — how many days after `AVAILABLE_FROM` a listing can still start (currently hardcoded to 30)
- [ ] Make `LAST_ONLINE_MAX_DAYS` overridable via env var (currently only in `config.py`)
- [ ] Add `RENT_TYPE` — `"warm"` / `"cold"` / `"both"` (currently hardcoded to both in `SEARCH_URL`)


## 6. Onboarding & usability

> Friction points for a new user setting this up from scratch.

- [ ] Add a `scripts/setup.py` that walks through config interactively and writes `.env`
- [ ] Add startup config validation — warn clearly if required fields (`TELEGRAM_BOT_TOKEN`, etc.) are missing instead of crashing mid-run
- [ ] Add a note in README / config explaining how to look up `CITY_ID` from a WG-Gesucht URL
- [ ] Add district examples for common German cities (Berlin, Munich, Frankfurt, Cologne) as commented-out blocks in `config.py`
