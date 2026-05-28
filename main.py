from dotenv import load_dotenv
load_dotenv()

from src.config import CRAWL_MAX_PAGES, HEADLESS
from src.crawler import crawl
from src.filters import run_checks, reject_reason
from src.seen import load_seen, mark_seen
from src.telegram import send, format_listing


def main():
    seen = load_seen()
    listings = crawl(max_pages=CRAWL_MAX_PAGES, headless=HEADLESS)

    new_matches: list[dict] = []
    seen_this_run: set[str] = set()

    for listing in listings:
        lid = listing["id"]
        if lid in seen or lid in seen_this_run:
            continue
        seen_this_run.add(lid)

        checks = run_checks(listing)
        passed = all(ok for _, _, ok in checks)

        print(f"\n  {listing['title']}")
        for name, value, ok in checks:
            print(f"    {'✓' if ok else '✗'} {name:<10} {value}")

        if passed:
            new_matches.append(listing)
            print(f"    → MATCH: {listing['url']}")
            send(format_listing(listing))

    print(f"\n{len(new_matches)} new matches out of {len(listings)} listings")

    if new_matches:
        print("\n--- Matches ---")
        for i, match in enumerate(new_matches, 1):
            print(f"  {i}. {match['price_text']:>8}  {match['title']}")
            print(f"           {match['location']}")
            print(f"           {match['date_text']}")
            print(f"           {match['url']}")


    mark_seen(seen, [l["id"] for l in listings])


if __name__ == "__main__":
    main()
