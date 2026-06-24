import re
from datetime import datetime

from src.config import (
    PREFERRED_DISTRICTS,
    DISTRICT_FALLBACK_CITY,
    DEFAULT_MAX_RENT,
    MOVE_IN_FROM,
    MOVE_IN_TO,
    STAY_UNTIL,
    LAST_ONLINE_MAX_DAYS,
    WG_SIZE_MAX,
    WG_FLATSHARE_TYPES,
)
from src.listing import Listing

MAX_RENT = DEFAULT_MAX_RENT
EARLIEST_MOVE_IN = datetime.strptime(MOVE_IN_FROM, "%Y-%m-%d")
LATEST_MOVE_IN = datetime.strptime(MOVE_IN_TO, "%Y-%m-%d")
MIN_END_DATE = datetime.strptime(STAY_UNTIL, "%Y-%m-%d")


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


def _dates_ok(start: str) -> bool:
    start_dt = _parse_date(start)
    if not start_dt:
        return True  # no start date: pass through rather than reject blindly
    return EARLIEST_MOVE_IN <= start_dt <= LATEST_MOVE_IN


def _end_date_ok(end: str) -> bool:
    end_dt = _parse_date(end)
    if not end_dt:
        return True  # open-ended listing: pass through
    return end_dt >= MIN_END_DATE


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


def run_checks(listing: Listing) -> list[tuple[str, str, bool]]:
    """Returns per-filter (name, display_value, passed) tuples for console reporting."""
    checks = [
        ("price",    listing.price_text,                                                          _price_ok(listing.price_text)),
        ("district", listing.location[:45].strip(),                                               _district_ok(listing.location + " " + listing.title)),
        ("dates",    f"{listing.date_start} – {listing.date_end}" if listing.date_start else "?", _dates_ok(listing.date_start)),
        ("end_date", listing.date_end or "open",                                                  _end_date_ok(listing.date_end)),
        ("online",   listing.last_online or "unknown",                                            _last_online_ok(listing.last_online)),
    ]
    if listing.wg_type_code:
        checks += [
            ("wg_size", listing.location[:45].strip(), _wg_size_ok(listing.location)),
            ("wg_type", listing.wg_type_code,          _wg_type_ok(listing.wg_type_code)),
        ]
    return checks
