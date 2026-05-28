# Deployment risk checklist

## Critical — will break in cloud

- [x] Add `--no-sandbox` / `--disable-setuid-sandbox` to every `chromium.launch()` call (`src/crawler.py`, `src/auth.py` ×2, `src/scraper.py`)
- [x] `DATA_DIR` is now configurable via env var — set it to a mounted persistent volume on cloud (`DATA_DIR=/mnt/data`)

## High — logic bugs

- [x] Add WG-Zimmer URL check to `run_checks()` in `src/filters.py` — new `type` row added, consistent with `reject_reason()`
- [x] Guard `ensure_session()` return value in `main.py` — aborts early with a clear error instead of crawling unauthenticated

## Medium — reliability / waste

- [x] Remove `python-telegram-bot` from `requirements.txt` — unused, ~100 MB pull-in
- [x] Fix race condition in `ai.py` `_get_client()` — wrapped with `threading.Lock()`

## Security — before any remote push

- [x] `.env` is gitignored and never committed (verified with `git log --all -- .env`)
- [ ] Inject secrets as platform environment variables on deploy target, not as a copied `.env` file
- [ ] Rotate credentials after first deployment as a precaution
