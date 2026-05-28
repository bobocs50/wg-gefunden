from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

load_dotenv()

from src.auth import ensure_session
from src.config import AI_ENABLED, CRAWL_MAX_PAGES, HEADLESS, MAX_AI_CALLS_PER_RUN
from src.crawler import crawl
from src.filters import run_checks
from src.seen import load_seen, mark_seen
from src.scraper import scrape_details
from src.ai import analyze
from src.telegram import send, format_listing, format_listing_with_ai


def main():
    if not ensure_session():
        print("ERROR: Could not establish a valid session — aborting")
        return
    seen = load_seen()
    listings = crawl(max_pages=CRAWL_MAX_PAGES, headless=HEADLESS)

    new_matches: list[dict] = []

    for listing in listings:
        lid = listing["id"]
        if lid in seen:
            print(f"\n  {listing['title']}")
            print(f"    ↷ already seen ({lid})")
            continue
        seen.add(lid)

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
                    if analysis:
                        print(f"  {match['title']}: match={analysis['recommendation_score']}/10  scam={analysis['scam_score']}/10  — {analysis.get('scam_reason', '')}")
                        send(format_listing_with_ai(match, analysis))
                    else:
                        send(format_listing(match))

            for match in basic_matches:
                send(format_listing(match))

    mark_seen(seen, [l["id"] for l in listings])


if __name__ == "__main__":
    main()
