import re
from datetime import datetime, timedelta

from src.config import (
    PREFERRED_DISTRICTS,
    DISTRICT_FALLBACK_CITY,
    DEFAULT_MAX_RENT,
    DEFAULT_AVAILABLE_FROM,
    DEFAULT_AVAILABLE_UNTIL,
    LAST_ONLINE_MAX_DAYS,
    WG_SIZE_MAX,
    WG_FLATSHARE_TYPES,
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
    if any(d in loc for d in PREFERRED_DISTRICTS):
        return True
    # Pass listings with no specific district — e.g. "1-Zimmer | Hamburg | Ifflandstraße"
    # where the city part is just the fallback city with no sub-district appended.
    return bool(DISTRICT_FALLBACK_CITY) and any(
        p.strip() == DISTRICT_FALLBACK_CITY for p in loc.split("|")
    )


def _dates_ok(start: str, end: str) -> bool:
    start_dt = _parse_date(start)
    if not start_dt:
        return True  # no start date: pass through rather than reject blindly
    if start_dt < AVAILABLE_FROM:
        return False  # starts before move-in date
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


def _wg_size_ok(location: str) -> bool:
    if WG_SIZE_MAX == 0:
        return True
    m = re.search(r'(\d+)er WG', location, re.IGNORECASE)
    if not m:
        return True
    return int(m.group(1)) <= WG_SIZE_MAX


def _wg_type_ok(wg_type_code: str) -> bool:
    if not WG_FLATSHARE_TYPES or not wg_type_code:
        return True
    return wg_type_code in WG_FLATSHARE_TYPES


def run_checks(listing: dict) -> list[tuple[str, str, bool]]:
    """Returns per-filter (name, display_value, passed) tuples for console reporting."""
    price_text = listing.get("price_text", "0")
    location = listing.get("location", "")
    d_start = listing.get("date_start", "")
    d_end = listing.get("date_end", "")
    last_online = listing.get("last_online", "")
    wg_type_code = listing.get("wg_type_code", "")
    checks = [
        ("price",    price_text,                                  _price_ok(price_text)),
        ("district", location[:45].strip(),                       _district_ok(location)),
        ("dates",    f"{d_start} – {d_end}" if d_start else "?", _dates_ok(d_start, d_end)),
        ("online",   last_online or "unknown",                    _last_online_ok(last_online)),
    ]
    if wg_type_code:
        checks += [
            ("wg_size", location[:45].strip(), _wg_size_ok(location)),
            ("wg_type", wg_type_code,          _wg_type_ok(wg_type_code)),
        ]
    return checks
