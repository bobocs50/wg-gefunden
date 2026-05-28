import re

from playwright.sync_api import sync_playwright, Page

from src.config import SESSION_FILE, MAX_DETAIL_CHARS

# CSS selectors for the main text sections on a WG-Gesucht listing detail page.
# Tried in order; all found sections are joined together.
_DETAIL_SELECTORS = [
    "#ad-description",
    "#house-description",
    "#landlord-description",
    ".panel-body",
]


def _extract_text(page: Page) -> str:
    parts: list[str] = []
    seen_text: set[str] = set()

    for selector in _DETAIL_SELECTORS:
        for el in page.locator(selector).all():
            try:
                text = re.sub(r'\s+', ' ', el.inner_text()).strip()
            except Exception:
                continue
            if text and text not in seen_text:
                seen_text.add(text)
                parts.append(text)

    return "\n\n".join(parts)[:MAX_DETAIL_CHARS]


def scrape_details(urls: list[str]) -> dict[str, str]:
    """Visit each listing URL and return {url: extracted_text}.

    Opens a single browser session for all URLs. Returns an empty string for
    any URL that fails to load.
    """
    results: dict[str, str] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = (
            browser.new_context(storage_state=str(SESSION_FILE))
            if SESSION_FILE.exists()
            else browser.new_context()
        )
        page = context.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        for url in urls:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1200)
                text = _extract_text(page)
                results[url] = text
                print(f"  scraped {len(text)} chars — {url}")
            except Exception as e:
                print(f"  scrape failed ({e}) — {url}")
                results[url] = ""

        browser.close()

    return results
