import os
import re

from playwright.sync_api import sync_playwright, Page, Locator

from src.auth import is_logged_in, login
from src.config import BASE_URL, SEARCH_URL, SESSION_FILE, DEFAULT_AVAILABLE_FROM, DEFAULT_AVAILABLE_UNTIL


def _iso_to_de(iso: str) -> str:
    """2026-08-15 → 15.08.2026"""
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def _paginated_url(base_url: str, page_index: int) -> str:
    offset = page_index * 20
    return re.sub(r'\.\d+\.html', f'.{offset}.html', base_url)


def _apply_filters(page: Page) -> str:
    """Click through the WG-Gesucht filter UI to set rent ceiling and date window.

    Returns the URL after filters are applied (used as base for pagination).
    """
    max_rent = os.getenv("MAX_RENT", "1500")
    date_from = _iso_to_de(os.getenv("AVAILABLE_FROM", DEFAULT_AVAILABLE_FROM))
    date_to = _iso_to_de(os.getenv("AVAILABLE_UNTIL", DEFAULT_AVAILABLE_UNTIL))

    # Deselect WG-Zimmer category if it came pre-selected
    page.locator("button[data-id='categories']").click()
    page.wait_for_timeout(600)
    wg_option = page.locator("ul.dropdown-menu.inner li[data-original-index='0']")
    if wg_option.count() and "selected" in (wg_option.get_attribute("class") or ""):
        wg_option.locator("a").click()
        page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    # Rent ceiling
    page.locator("button.dropdown_form_toggle[data-target='#rent_filter_dropdown_form']").click()
    page.wait_for_timeout(800)
    rent_input = page.locator("#rent_filter_dropdown_form input.max_rent_input[data-input='rMax']").first
    rent_input.click(click_count=3)
    rent_input.type(max_rent)
    page.wait_for_timeout(300)
    page.locator("button.filter_form_submit[data-form='#rent_filter_dropdown_form']").click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)

    # Date window
    page.locator(".hidden-xs.hidden-sm button[data-target='#extra_filters_form']").click()
    page.wait_for_timeout(800)
    from_el = page.locator("#date_from")
    from_el.click(click_count=3)
    from_el.type(date_from)
    page.wait_for_timeout(300)
    to_el = page.locator("#date_to")
    to_el.click(click_count=3)
    to_el.type(date_to)
    page.wait_for_timeout(300)
    page.locator("button.filter_form_submit[data-form='#extra_filters_form']").click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)

    return page.url


def _parse_card(card: Locator) -> dict | None:
    """Extract a listing dict from a search result card. Returns None for ads or empty cards."""
    card_id = card.get_attribute("id") or ""
    id_match = re.search(r'\d+$', card_id)
    if not id_match:
        return None

    link = card.locator("h2.truncate_title a, h3.truncate_title a").first
    title = link.inner_text().strip() if link.count() else ""
    href = link.get_attribute("href") if link.count() else ""
    url = (BASE_URL + href) if href and href.startswith("/") else (href or "")

    if not title or "wg-gesucht.de" not in url:
        return None  # empty card or partner ad (e.g. Wunderflats)

    price_el = card.locator(".col-xs-3 b").first
    price_text = price_el.inner_text().strip() if price_el.count() else ""

    loc_el = card.locator(".col-xs-11 span").first
    location = re.sub(r'\s+', ' ', loc_el.inner_text().strip() if loc_el.count() else "")

    date_el = card.locator(".col-xs-5.text-center").first
    date_text = re.sub(r'\s+', ' ', date_el.inner_text().strip() if date_el.count() else "")

    online_el = card.locator(".col-sm-12.flex_space_between span[style*='color']").first
    online_text = online_el.inner_text().strip() if online_el.count() else ""
    online_match = re.search(r'Online:\s*(\d{2}\.\d{2}\.\d{4})', online_text)

    date_parts = re.findall(r'\d{2}\.\d{2}\.\d{4}', date_text)
    return {
        "id": id_match.group(),
        "title": title,
        "price_text": price_text,
        "location": location,
        "date_text": date_text,
        "date_start": date_parts[0] if len(date_parts) > 0 else "",
        "date_end": date_parts[1] if len(date_parts) > 1 else "",
        "last_online": online_match.group(1) if online_match else "",
        "url": url,
    }


def _scrape_page(page: Page) -> list[dict]:
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)
    cards = page.locator("div[id^='liste-details-ad-']").all()
    return [listing for card in cards if (listing := _parse_card(card))]


def crawl(max_pages: int = 3, headless: bool = False) -> list[dict]:
    all_listings: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        if SESSION_FILE.exists():
            context = browser.new_context(storage_state=str(SESSION_FILE))
        else:
            context = browser.new_context()
            print("WARNING: No session file — crawling without login")

        page = context.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})
        page.goto(SEARCH_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        if not is_logged_in(page):
            login(page, context)
            page.goto(SEARCH_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)

        filtered_url = _apply_filters(page)
        print(f"Filters applied — {filtered_url}")

        for i in range(max_pages):
            if i > 0:
                page.goto(_paginated_url(filtered_url, i), wait_until="domcontentloaded")

            listings = _scrape_page(page)
            print(f"  page {i + 1}: {len(listings)} listings")
            if not listings:
                break
            all_listings.extend(listings)

        browser.close()

    return all_listings
