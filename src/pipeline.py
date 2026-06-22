from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from src.ai import analyze, draft_application
from src.config import AI_ENABLED, MAX_AI_CALLS_PER_RUN
from src.filters import run_checks
from src.listing import Listing
from src.scraper import scrape_details
from src.telegram import format_listing, format_listing_with_ai, send


@dataclass
class ProcessResult:
    new_listings: int
    matches: int
    ai_calls: int


def process(listings: list[Listing], seen: set[str]) -> ProcessResult:
    """Filter, analyse, and notify for a batch of crawled listings.

    Does not modify `seen` — the caller owns seen-ID persistence.
    """
    new_listings = 0
    new_matches: list[Listing] = []

    for listing in listings:
        if listing.id in seen:
            print(f"\n  {listing.title}")
            print(f"    ↷ already seen ({listing.id})")
            continue
        new_listings += 1

        checks = run_checks(listing)
        passed = all(ok for _, _, ok in checks)

        print(f"\n  {listing.title}")
        for name, value, ok in checks:
            print(f"    {'✓' if ok else '✗'} {name:<10} {value}")

        if passed:
            new_matches.append(listing)
            print(f"    → MATCH")

    print(f"\n{len(new_matches)} new matches out of {len(listings)} listings")

    if not new_matches:
        return ProcessResult(new_listings=new_listings, matches=0, ai_calls=0)

    if not AI_ENABLED:
        print("AI disabled — sending basic alerts only")
        for match in new_matches:
            send(format_listing(match))
        return ProcessResult(new_listings=new_listings, matches=len(new_matches), ai_calls=0)

    ai_matches = new_matches[:MAX_AI_CALLS_PER_RUN]
    basic_matches = new_matches[MAX_AI_CALLS_PER_RUN:]
    print(
        f"AI enabled — analysing {len(ai_matches)} listing(s), "
        f"skipping {len(basic_matches)} due to cap"
    )

    ai_calls = 0

    if ai_matches:
        print("\nScraping detail pages...")
        details = scrape_details([m.url for m in ai_matches])

        print("Running AI analysis...")
        with ThreadPoolExecutor(max_workers=MAX_AI_CALLS_PER_RUN) as ex:
            futures = [(m, ex.submit(analyze, m, details.get(m.url, ""))) for m in ai_matches]

        for match, fut in futures:
            analysis = fut.result()
            ai_calls += 1
            if analysis:
                print(
                    f"  {match.title}: match={analysis['recommendation_score']}/10"
                    f"  scam={analysis['scam_score']}/10  — {analysis.get('scam_reason', '')}"
                )
                send(format_listing_with_ai(match, analysis))
            else:
                send(format_listing(match))
            draft = draft_application(match, details.get(match.url, ""))
            if draft:
                send(draft)

    for match in basic_matches:
        send(format_listing(match))

    return ProcessResult(new_listings=new_listings, matches=len(new_matches), ai_calls=ai_calls)
