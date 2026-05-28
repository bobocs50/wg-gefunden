"""
Load session, navigate to your actual search URL, dump HTML for selector inspection.
"""
import sys, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from playwright.sync_api import sync_playwright

SESSION_FILE = Path("data/session.json")
SEARCH_URL = "https://www.wg-gesucht.de/1-zimmer-wohnungen-und-wohnungen-und-haeuser-in-Hamburg.55.1+2+3.1.0.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=str(SESSION_FILE))
    page = context.new_page()

    print(f"Navigating to: {SEARCH_URL}")
    page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    print(f"URL after load: {page.url}")
    print(f"Title:          {page.title()}")

    html = page.content()
    out = Path("data/search_page.html")
    out.write_text(html, encoding="utf-8")
    print(f"HTML saved ({len(html):,} chars)")

    # Scan for any listing-like elements
    print("\n--- Listing container candidates ---")
    for sel in [
        "div[id^='liste-details-ad-']",
        ".wgg_card",
        ".offer_list_item",
        "[id^='angebot']",
        "article",
        "[data-id]",
        "li.offer",
        "[class*='offer']",
        "[class*='result']",
        "[class*='listing']",
        "[class*='tile']",
        "[class*='card']",
    ]:
        count = page.locator(sel).count()
        if count:
            first_html = page.locator(sel).first.inner_html()[:500]
            print(f"\n  {sel}: {count} elements")
            print(f"    {first_html!r}")

    # Dump #main_column
    print("\n--- #main_column (first 4000 chars) ---")
    mc = page.locator("#main_column").first
    if mc.count():
        print(mc.inner_html()[:4000])

    browser.close()
    print("\nDone.")
