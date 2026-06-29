"""
Kleinanzeigen Hamburg apartment scanner.

Crawls search results with Playwright, applies hard filters, runs AI analysis via
the project's existing src/ai.py, and sends Telegram notifications for matches.
Run directly: venv/bin/python3 scripts/kleinanzeigen_scan.py
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from playwright.sync_api import Page, BrowserContext, sync_playwright

from src.listing import Listing
from src.config import (
    DEFAULT_MAX_RENT,
    PREFERRED_DISTRICTS,
    STAY_UNTIL,
    AI_ENABLED,
    MAX_AI_CALLS_PER_RUN,
    MAX_DETAIL_CHARS,
    DATA_DIR,
    HEADLESS,
)
from src import ai, telegram

# ─── Constants ────────────────────────────────────────────────────────────────

SEEN_FILE = DATA_DIR / "seen_kleinanzeigen.json"
BASE_URL = "https://www.kleinanzeigen.de"
MAX_PAGES = 2
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# ─── Seen-ID persistence ──────────────────────────────────────────────────────

def _load_seen() -> set[str]:
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()


def _save_seen(existing: set[str], new_ids: set[str]) -> None:
    merged = existing | new_ids
    SEEN_FILE.write_text(json.dumps(sorted(merged)))
    print(f"Saved {len(merged)} seen IDs ({len(new_ids)} new)")


# ─── URL helpers ──────────────────────────────────────────────────────────────

def _search_url(page_num: int) -> str:
    base = f"{BASE_URL}/s-wohnung-mieten/hamburg/preis::{DEFAULT_MAX_RENT}/c203l9409"
    if page_num == 1:
        return f"{base}?sortingField=SORTING_DATE"
    return f"{base}/seite:{page_num}?sortingField=SORTING_DATE"


# ─── Browser helpers ──────────────────────────────────────────────────────────

def _dismiss_cookie_banner(page: Page) -> None:
    selectors = [
        "#gdpr-banner-accept",
        "button[id*='accept']",
        "button[class*='accept-all']",
        ".gdpr-accept-btn",
        "[data-testid='gdpr-banner-accept']",
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Zustimmen')",
        "button:has-text('Accept')",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() and btn.is_visible():
                btn.click()
                page.wait_for_timeout(800)
                return
        except Exception:
            pass


def _new_browser_context(playwright) -> tuple:
    browser = playwright.chromium.launch(
        headless=HEADLESS,
        args=["--no-sandbox", "--disable-setuid-sandbox"],
    )
    context = browser.new_context(
        user_agent=_UA,
        viewport={"width": 1280, "height": 900},
        locale="de-DE",
        extra_http_headers={"Accept-Language": "de-DE,de;q=0.9"},
    )
    return browser, context


# ─── Search page parsing ──────────────────────────────────────────────────────

def _parse_cards(page: Page) -> list[dict]:
    """Extract listing metadata from all article cards on the current search page."""
    # Wait for at least one card to appear (handles JS-rendered listings and post-cookie reflows)
    try:
        page.wait_for_selector("article.aditem", timeout=15000)
    except Exception:
        page.wait_for_timeout(3000)

    cards = page.locator("article.aditem").all()
    if not cards:
        cards = page.locator("li.ad-listitem article").all()

    listings = []
    for card in cards:
        try:
            # ID and URL come from data attributes — more reliable than parsing the href regex
            listing_id = card.get_attribute("data-adid") or ""
            href = card.get_attribute("data-href") or ""
            if not listing_id or not href or "/s-anzeige/" not in href:
                continue
            # Only keep listings in category 203 (Wohnung mieten) — rejects promoted
            # ads from bikes, products, and "Suche:" wanted ads that appear on the page.
            if "-203-" not in href:
                continue

            link = card.locator("a.ellipsis").first
            if not link.count():
                link = card.locator("h2 a, .text-module-begin a").first
            title = link.inner_text(timeout=3000).strip() if link.count() else ""
            if not title:
                continue

            price_el = card.locator(".aditem-main--middle--price-shipping--price").first
            price_text = price_el.inner_text(timeout=2000).strip() if price_el.count() else ""

            loc_el = card.locator(".aditem-main--top--left").first
            location = loc_el.inner_text(timeout=2000).strip() if loc_el.count() else ""
            location = re.sub(r"\s+", " ", location).strip()

            date_el = card.locator(".aditem-main--top--right").first
            date_text = date_el.inner_text(timeout=2000).strip() if date_el.count() else ""

            listings.append({
                "id": listing_id,
                "title": title,
                "price_text": price_text,
                "location": location,
                "date_text": date_text,
                "date_start": "",
                "date_end": "",
                "url": (BASE_URL + href) if href.startswith("/") else href,
                "href": href,
            })
        except Exception as e:
            print(f"  Card parse error: {e}")

    return listings


# ─── Hard filters ─────────────────────────────────────────────────────────────

def _price_ok(price_text: str) -> bool:
    """True if price is ≤ max_rent, or if price is unknown (pass through)."""
    match = re.search(r"([\d.]+)\s*€", price_text.replace(".", "").replace(",", "."))
    if not match:
        return True  # unknown price → pass
    try:
        return int(float(match.group(1))) <= DEFAULT_MAX_RENT
    except ValueError:
        return True


def _district_ok(location: str) -> bool:
    """True if location contains a preferred district, or is just 'Hamburg'."""
    loc_lower = location.lower()
    if re.fullmatch(r"hamburg\s*", loc_lower):
        return True
    return any(d in loc_lower for d in PREFERRED_DISTRICTS)


def _type_ok(title: str) -> bool:
    """Reject apartment swaps, wanted ads, and non-apartment listings."""
    lower = title.lower()
    reject_keywords = [
        "tauschwohnung", "wohnungsswap", "wohnungstausch",
        "suche wohnung", "wohnung gesucht",
        "gesuch:", "gesuch ",  # "Gesuch: Mietwohnung..." wanted ads
    ]
    return not any(kw in lower for kw in reject_keywords)


# ─── Detail page scraping and filters ─────────────────────────────────────────

def _scrape_detail(page: Page, url: str) -> str:
    """Fetch detail page and return combined text (dates + description)."""
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)

    parts: list[str] = []

    # Detail attributes (dates, size, etc.)
    for sel in ["#viewad-details", ".boxedarticle--details", "section.addetailspage"]:
        el = page.locator(sel).first
        if el.count():
            try:
                parts.append(el.inner_text(timeout=3000).strip())
            except Exception:
                pass
            break

    # Main description
    for sel in [
        "#viewad-description-text",
        "#viewad-description",
        ".ad-description",
        ".textcontent",
        "section[itemprop='description']",
    ]:
        el = page.locator(sel).first
        if el.count():
            try:
                parts.append(el.inner_text(timeout=5000).strip())
            except Exception:
                pass
            break

    combined = "\n\n".join(p for p in parts if p)
    return combined[:MAX_DETAIL_CHARS]


def _end_date_ok(detail_text: str) -> bool:
    """Return False if listing explicitly states an end date before STAY_UNTIL."""
    stay_dt = datetime.strptime(STAY_UNTIL, "%Y-%m-%d")
    patterns = [
        r"bis\s+(\d{1,2}\.\d{1,2}\.\d{4})",
        r"frei bis\s+(\d{1,2}\.\d{1,2}\.\d{4})",
        r"Ende\s+(\d{1,2}\.\d{1,2}\.\d{4})",
        r"Mietende[:\s]+(\d{1,2}\.\d{1,2}\.\d{4})",
        r"available until\s+(\d{1,2}\.\d{1,2}\.\d{4})",
        r"verfügbar bis\s+(\d{1,2}\.\d{1,2}\.\d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, detail_text, re.IGNORECASE)
        if m:
            raw = m.group(1)
            dm = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", raw)
            if dm:
                try:
                    end_dt = datetime(int(dm.group(3)), int(dm.group(2)), int(dm.group(1)))
                    if end_dt < stay_dt:
                        return False
                except ValueError:
                    pass
    return True


def _scam_precheck_ok(detail_text: str) -> bool:
    """Return False if obvious scam signals are present."""
    lower = detail_text.lower()
    red_flags = [
        "whatsapp only",
        "nur whatsapp",
        "contact via whatsapp",
        "western union",
        "moneygram",
        "vorauszahlung",
        "advance payment",
        "upfront payment",
        "wire transfer",
    ]
    return not any(flag in lower for flag in red_flags)


# ─── Telegram formatting ──────────────────────────────────────────────────────

def _format_no_ai(listing: dict) -> str:
    url = listing["url"]
    return (
        f"🏠 <b>{listing['title']}</b>\n"
        f"💶 {listing['price_text'] or 'N/A'}  ·  📅 {listing['date_text'] or 'N/A'}\n"
        f"📍 {listing['location'] or 'Hamburg'}\n"
        f"\n"
        f"🔗 <a href=\"{url}\">{url}</a>"
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def run() -> None:
    seen = _load_seen()
    all_ids: set[str] = set()
    matches: list[dict] = []
    total_found = 0
    total_new = 0

    with sync_playwright() as p:
        browser, context = _new_browser_context(p)
        search_page = context.new_page()
        detail_page = context.new_page()

        try:
            for page_num in range(1, MAX_PAGES + 1):
                url = _search_url(page_num)
                print(f"\nPage {page_num}: {url}")
                search_page.goto(url, wait_until="domcontentloaded", timeout=30000)

                if page_num == 1:
                    _dismiss_cookie_banner(search_page)
                    page_title = search_page.title()
                    print(f"  Page title: {page_title}")

                cards = _parse_cards(search_page)
                print(f"  {len(cards)} cards found")

                if not cards:
                    # Might be blocked or CAPTCHA — dump page title for diagnosis
                    print(f"  WARNING: no cards — possible bot detection")
                    print(f"  Title: {search_page.title()}")
                    break

                total_found += len(cards)

                for listing in cards:
                    lid = listing["id"]
                    all_ids.add(lid)

                    if lid in seen:
                        continue
                    total_new += 1

                    if not _price_ok(listing["price_text"]):
                        print(f"  ✗ price  {listing['title'][:50]}")
                        continue

                    if not _district_ok(listing["location"]):
                        print(f"  ✗ district  {listing['location']}  ({listing['title'][:40]})")
                        continue

                    if not _type_ok(listing["title"]):
                        print(f"  ✗ type     {listing['title'][:60]}")
                        continue

                    print(f"  → detail  {listing['title'][:60]}")
                    try:
                        detail_text = _scrape_detail(detail_page, listing["url"])
                    except Exception as e:
                        print(f"    detail fetch failed: {e}")
                        detail_text = ""

                    if not _end_date_ok(detail_text):
                        print(f"    ✗ end date before {STAY_UNTIL}")
                        continue

                    if not _scam_precheck_ok(detail_text):
                        print(f"    ✗ scam flag in description")
                        continue

                    listing["detail_text"] = detail_text
                    matches.append(listing)

        finally:
            browser.close()

    # ── AI analysis + Telegram ────────────────────────────────────────────────
    notifications_sent = 0
    ai_calls = 0

    for listing in matches:
        detail_text = listing.get("detail_text", "")
        analysis = None

        if AI_ENABLED and ai_calls < MAX_AI_CALLS_PER_RUN:
            listing_obj = Listing(
                id=listing["id"],
                title=listing["title"],
                price_text=listing["price_text"],
                location=listing["location"],
                date_text=listing["date_text"],
                date_start=listing.get("date_start", ""),
                date_end=listing.get("date_end", ""),
                last_online="",
                url=listing["url"],
                wg_type_code="",
            )
            analysis = ai.analyze(listing_obj, detail_text)
            ai_calls += 1

        if analysis:
            scam = analysis.get("scam_score", 10)
            match_score = analysis.get("recommendation_score", 0)
            print(f"  AI scam={scam} match={match_score}  {listing['title'][:50]}")
            if scam > 3 or match_score < 4:
                print(f"    ✗ below threshold")
                continue
            msg = telegram.format_listing_with_ai(listing_obj, analysis)
        else:
            msg = _format_no_ai(listing)

        if telegram.send(msg):
            notifications_sent += 1
            print(f"  📨 sent: {listing['title'][:60]}")

    _save_seen(seen, all_ids)
    print(
        f"\nKleinanzeigen: {total_found} listings found · "
        f"{total_new} new · "
        f"{len(matches)} passed filters · "
        f"{notifications_sent} notifications sent"
    )


if __name__ == "__main__":
    run()
