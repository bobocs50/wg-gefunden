from dataclasses import dataclass


@dataclass(frozen=True)
class Listing:
    id: str
    title: str
    price_text: str
    location: str
    date_text: str
    date_start: str   # "DD.MM.YYYY" or ""
    date_end: str     # "DD.MM.YYYY" or ""
    last_online: str  # "DD.MM.YYYY" or ""
    url: str
    wg_type_code: str
