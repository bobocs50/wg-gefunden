import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from playwright.sync_api import Page, Locator

from src.browser import authenticated_page
from src.config import (
    BASE_URL,
    SEARCH_URL,
    DEFAULT_AVAILABLE_FROM,
    DEFAULT_AVAILABLE_UNTIL,
    DEFAULT_MAX_RENT,
    SEARCH_CATEGORY_INDICES,
    SEARCH_WG,
    WG_SIZE_MAX,
    WG_FLATSHARE_TYPES,
    FURNISHED_ONLY,
    CRAWL_MAX_PAGES,
    HEADLESS,
)


def _iso_to_de(iso: str) -> str:
    """2026-08-15 → 15.08.2026"""
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def _iso_to_unix(iso_date: str) -> int:
    """YYYY-MM-DD → Unix timestamp at midnight Germany local time (CET/CEST)."""
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    offset = 2 if 3 < dt.month < 10 else 1  # CEST Apr–Sep, CET Oct–Mar
    return int(dt.replace(tzinfo=timezone(timedelta(hours=offset))).timestamp())


def _paginated_url(base_url: str, page_index: int) -> str:
    offset = page_index * 20
    return re.sub(r'\.\d+\.html', f'.{offset}.html', base_url)


def _dismiss_cookie_banner(page: Page) -> None:
    try:
        page.wait_for_selector("a.cmptxt_btn_yes", timeout=5000)
        page.click("a.cmptxt_btn_yes")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1000)
    except Exception:
        pass


def _apply_filters(page: Page) -> str:
    """Click through the WG-Gesucht filter UI to set rent ceiling and date window.

    Returns the URL after filters are applied (used as base for pagination).
    """
    max_rent = str(DEFAULT_MAX_RENT)

    _dismiss_cookie_banner(page)

    # Set categories to exactly SEARCH_CATEGORY_INDICES
    page.locator("button[data-id='categories']").click()
    page.wait_for_timeout(600)
    for i in range(4):
        option = page.locator(f"ul.dropdown-menu.inner li[data-original-index='{i}']")
        if not option.count():
            continue
        is_selected = "selected" in (option.get_attribute("class") or "")
        want_selected = i in SEARCH_CATEGORY_INDICES
        if is_selected != want_selected:
            option.locator("a").click()
            page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    # Furnished filter — index 0=egal, 1=Ja, 2=Nein
    if FURNISHED_ONLY:
        page.locator("button[data-id='furnished']").click()
        page.wait_for_timeout(400)
        page.locator("ul.dropdown-menu.inner li[data-original-index='1']").locator("a").click()
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

    # Date window — inject timestamps directly into the URL to bypass the datepicker UI
    parsed = urlparse(page.url)
    # parse_qs returns lists; preserve all values (e.g. categories[]=1&categories[]=2)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params["dFr"] = [str(_iso_to_unix(DEFAULT_AVAILABLE_FROM))]
    params["dTo"] = [str(_iso_to_unix(DEFAULT_AVAILABLE_UNTIL))]
    if SEARCH_WG and WG_SIZE_MAX > 0:
        params["wg_flatmates_to"] = [str(WG_SIZE_MAX)]
    if SEARCH_WG and WG_FLATSHARE_TYPES:
        params["flatshare_types[]"] = WG_FLATSHARE_TYPES
    date_url = urlunparse(parsed._replace(query=urlencode(params, doseq=True)))
    page.goto(date_url, wait_until="domcontentloaded")
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
    # If the URL is a search redirect (?asset_id=...), keep it as-is —
    # Playwright will follow the redirect to the real listing page.

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

    type_el = card.locator("[data-filter-value]").first
    wg_type_code = type_el.get_attribute("data-filter-value") if type_el.count() else ""

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
        "wg_type_code": wg_type_code or "",
    }


def _scrape_page(page: Page) -> list[dict]:
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)
    cards = page.locator("div[id^='liste-details-ad-']").all()
    return [listing for card in cards if (listing := _parse_card(card))]


def crawl(max_pages: int = CRAWL_MAX_PAGES, headless: bool = HEADLESS) -> list[dict]:
    all_listings: list[dict] = []

    with authenticated_page(headless=headless) as page:
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

    return all_listings
