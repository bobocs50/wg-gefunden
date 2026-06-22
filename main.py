import os
import sys

from dotenv import load_dotenv

load_dotenv()

from src.auth import ensure_session
from src.config import AI_ENABLED, CRAWL_MAX_PAGES, HEADLESS
from src.crawler import crawl
from src.pipeline import process
from src.seen import load_seen, save_seen
from src.stats import record_run
from src.telegram import send


def _validate_env() -> None:
    missing = []
    for var in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        if not os.getenv(var):
            missing.append(var)
    if AI_ENABLED and not os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY  (required when ai.enabled = true in config.toml)")
    if missing:
        print("ERROR: Missing required environment variables:")
        for v in missing:
            print(f"  • {v}")
        print("Copy .env.example to .env and fill in the missing values.")
        sys.exit(1)


def main():
    _validate_env()
    errors: list[str] = []

    session_ok, relogged = ensure_session()
    if not session_ok:
        msg = "ERROR: Could not establish a valid session — aborting"
        print(msg)
        errors.append("session_failed")
        record_run(listings_scraped=0, new_listings=0, matches=0, relogged=relogged, errors=errors, ai_calls=0)
        send("🔐 <b>WG-Gesucht bot login failed</b>\n\nCould not log in after session expired. Bot is not running. Check credentials or re-run <code>scripts/login.py</code> on the server.")
        return

    seen = load_seen()
    try:
        listings = crawl(max_pages=CRAWL_MAX_PAGES, headless=HEADLESS)
    except Exception as e:
        print(f"Crawl failed ({e}) — retrying once...")
        errors.append(f"crawl_failed: {e}")
        try:
            listings = crawl(max_pages=CRAWL_MAX_PAGES, headless=HEADLESS)
        except Exception as e2:
            print(f"Crawl failed again ({e2}) — aborting")
            errors.append(f"crawl_failed_retry: {e2}")
            record_run(listings_scraped=0, new_listings=0, matches=0, relogged=relogged, errors=errors, ai_calls=0)
            return

    # Persist all scraped IDs immediately — a crash during AI analysis won't lose them
    save_seen(seen | {l.id for l in listings})

    result = process(listings, seen)

    record_run(
        listings_scraped=len(listings),
        new_listings=result.new_listings,
        matches=result.matches,
        relogged=relogged,
        errors=errors,
        ai_calls=result.ai_calls,
    )


if __name__ == "__main__":
    main()
