import os
import sys
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

load_dotenv()

from src.auth import ensure_session
from src.config import AI_ENABLED, CRAWL_MAX_PAGES, HEADLESS, MAX_AI_CALLS_PER_RUN
from src.crawler import crawl
from src.filters import run_checks
from src.seen import load_seen, save_seen
from src.scraper import scrape_details
from src.ai import analyze, draft_application
from src.telegram import send, format_listing, format_listing_with_ai
from src.stats import record_run


def _validate_env() -> None:
    missing = []
    for var in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        if not os.getenv(var):
            missing.append(var)
    if AI_ENABLED and not os.getenv("GEMINI_API_KEY"):
        missing.append("GEMINI_API_KEY  (required when ai.enabled = true in config.toml)")
    if missing:
        print("ERROR: Missing required environment variables:")
        for v in missing:
            print(f"  • {v}")
        print("Copy .env.example to .env and fill in the missing values.")
        sys.exit(1)


def main():
    _validate_env()
    errors: list[str] = []
    ai_calls = 0

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
    save_seen(seen | {l["id"] for l in listings})

    new_listings = 0
    new_matches: list[dict] = []

    for listing in listings:
        lid = listing["id"]
        if lid in seen:
            print(f"\n  {listing['title']}")
            print(f"    ↷ already seen ({lid})")
            continue
        seen.add(lid)
        new_listings += 1

        checks = run_checks(listing)
        passed = all(ok for _, _, ok in checks)

        print(f"\n  {listing['title']}")
        for name, value, ok in checks:
            print(f"    {'✓' if ok else '✗'} {name:<10} {value}")

        if passed:
            new_matches.append(listing)
            print(f"    → MATCH")

    print(f"\n{len(new_matches)} new matches out of {len(listings)} listings")

    if new_matches:
        if not AI_ENABLED:
            print("AI disabled — sending basic alerts only")
            for match in new_matches:
                send(format_listing(match))
        else:
            ai_matches = new_matches[:MAX_AI_CALLS_PER_RUN]
            basic_matches = new_matches[MAX_AI_CALLS_PER_RUN:]
            print(
                f"AI enabled — analysing {len(ai_matches)} listing(s), "
                f"skipping {len(basic_matches)} due to cap"
            )

            details: dict[str, str] = {}
            if ai_matches:
                print("\nScraping detail pages...")
                details = scrape_details([m["url"] for m in ai_matches])

                print("Running AI analysis...")
                with ThreadPoolExecutor(max_workers=MAX_AI_CALLS_PER_RUN) as ex:
                    futures = [
                        (m, ex.submit(analyze, m, details.get(m["url"], "")))
                        for m in ai_matches
                    ]
                for match, fut in futures:
                    analysis = fut.result()
                    ai_calls += 1
                    if analysis:
                        print(f"  {match['title']}: match={analysis['recommendation_score']}/10  scam={analysis['scam_score']}/10  — {analysis.get('scam_reason', '')}")
                        send(format_listing_with_ai(match, analysis))
                    else:
                        send(format_listing(match))
                    draft = draft_application(match, details.get(match["url"], ""))
                    if draft:
                        send(draft)

            for match in basic_matches:
                send(format_listing(match))

    record_run(
        listings_scraped=len(listings),
        new_listings=new_listings,
        matches=len(new_matches),
        relogged=relogged,
        errors=errors,
        ai_calls=ai_calls,
    )


if __name__ == "__main__":
    main()
