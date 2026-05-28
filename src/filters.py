import re
from datetime import datetime, timedelta

from src.config import (
    PREFERRED_DISTRICTS,
    DEFAULT_MAX_RENT,
    DEFAULT_AVAILABLE_FROM,
    DEFAULT_AVAILABLE_UNTIL,
    LAST_ONLINE_MAX_DAYS,
)

MAX_RENT = DEFAULT_MAX_RENT
AVAILABLE_FROM = datetime.strptime(DEFAULT_AVAILABLE_FROM, "%Y-%m-%d")
AVAILABLE_UNTIL = datetime.strptime(DEFAULT_AVAILABLE_UNTIL, "%Y-%m-%d")


def _parse_date(value: str) -> datetime | None:
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _price_ok(price_text: str) -> bool:
    digits = re.sub(r"[^\d]", "", price_text)
    price = int(digits) if digits else 0
    return 0 < price <= MAX_RENT


def _district_ok(location: str) -> bool:
    loc = location.lower()
    return any(d in loc for d in PREFERRED_DISTRICTS)


def _dates_ok(start: str, end: str) -> bool:
    start_dt = _parse_date(start)
    if not start_dt:
        return True  # no start date: pass through rather than reject blindly
    if start_dt > AVAILABLE_FROM + timedelta(days=30):
        return False  # starts too late for move-in window
    end_dt = _parse_date(end)
    if not end_dt:
        return True  # open-ended contract: assume long-term, good enough
    return end_dt >= AVAILABLE_UNTIL


def _last_online_ok(last_online: str) -> bool:
    if not last_online:
        return True  # unknown: pass through
    dt = _parse_date(last_online)
    return not dt or (datetime.now() - dt).days <= LAST_ONLINE_MAX_DAYS


def reject_reason(listing: dict) -> str | None:
    """Returns a short description of the first failing filter, or None if the listing passes all."""
    if "/wg-zimmer-in-" in listing.get("url", ""):
        return "flatshare (WG-Zimmer)"
    if not _price_ok(listing.get("price_text", "0")):
        return f"price ({listing.get('price_text', '?')})"
    if not _district_ok(listing.get("location", "")):
        return f"district ({listing.get('location', '?')[:40].strip()})"
    if not _dates_ok(listing.get("date_start", ""), listing.get("date_end", "")):
        return f"dates ({listing.get('date_start', '?')} – {listing.get('date_end', '?')})"
    if not _last_online_ok(listing.get("last_online", "")):
        return f"inactive (online: {listing.get('last_online', '?')})"
    return None


def _type_ok(url: str) -> bool:
    return "/wg-zimmer-in-" not in url


def run_checks(listing: dict) -> list[tuple[str, str, bool]]:
    """Returns per-filter (name, display_value, passed) tuples for console reporting."""
    url = listing.get("url", "")
    price_text = listing.get("price_text", "0")
    location = listing.get("location", "")
    d_start = listing.get("date_start", "")
    d_end = listing.get("date_end", "")
    last_online = listing.get("last_online", "")
    return [
        ("type",     "flatshare" if not _type_ok(url) else "ok", _type_ok(url)),
        ("price",    price_text,                                  _price_ok(price_text)),
        ("district", location[:45].strip(),                       _district_ok(location)),
        ("dates",    f"{d_start} – {d_end}" if d_start else "?", _dates_ok(d_start, d_end)),
        ("online",   last_online or "unknown",                    _last_online_ok(last_online)),
    ]
