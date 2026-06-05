# Rebuild Guide — Listing Type, WG Size & WG Gender Filters

Three connected settings that control what kind of listings are accepted.

---

## 1. Listing Category — WG room vs. apartment

Controlled by the `categories[]` params in the search URL in `src/config.py`:

```python
# categories[]: 0 = WG-Zimmer, 1 = 1-Zimmer-Wohnung, 2 = Wohnung (full flat)
SEARCH_URL = (
    "https://www.wg-gesucht.de/wg-zimmer-und-1-zimmer-wohnungen-und-wohnungen-in-Muenster.91.0+1+2.1.0.html"
    "?categories%5B%5D=0&categories%5B%5D=1&categories%5B%5D=2"
    "..."
)
```

- Include `categories[]=0` → WG rooms
- Include `categories[]=1` → 1-room apartments
- Include `categories[]=2` → full apartments
- Remove any of those to exclude that category entirely

This is purely a URL parameter — no extra filter code needed. The URL slug also encodes this (the `0+1+2` segment), but only the query params matter for the server filter.

---

## 2. WG Size — `WG_SIZE_MAX`

**`src/config.py`**

```python
def _int_env(name: str, default: int, minimum: int | None = None) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    if minimum is not None:
        return max(minimum, parsed)
    return parsed

# 0 = no limit; 3 = accept up to 3-person WGs (default)
WG_SIZE_MAX: int = _int_env("WG_SIZE_MAX", 3, minimum=0)
```

Override via `.env`: `WG_SIZE_MAX=4`

**`src/filters.py`** — the Python check:

```python
def _wg_size_ok(location: str) -> bool:
    if WG_SIZE_MAX == 0:
        return True
    m = re.search(r'(\d+)er WG', location, re.IGNORECASE)
    if not m:
        return True  # size not mentioned → pass through
    return int(m.group(1)) <= WG_SIZE_MAX
```

The location string on listing cards contains e.g. `"Münster | Mauritz | 3er WG"`. The regex picks out the number.

**`src/crawler.py`** — also injected into the search URL before scraping:

```python
if WG_SIZE_MAX > 0:
    param_list.append(("wg_flatmates_to", str(WG_SIZE_MAX)))
```

---

## 3. WG Gender / Type — `WG_FLATSHARE_TYPES`

**`src/config.py`**

```python
def _list_env(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [v.strip() for v in value.split(",") if v.strip()]

# Default: women-only + mixed only. Empty list = accept all types.
WG_FLATSHARE_TYPES: list[str] = _list_env("WG_FLATSHARE_TYPES", ["2", "12"])
```

Override via `.env`: `WG_FLATSHARE_TYPES=2,12,1`

**All WG-Gesucht type codes:**

| Code | Type |
|------|------|
| `2`  | Frauen-WG (women-only) |
| `12` | gemischte WG (mixed) |
| `3`  | Männer-WG (men-only) |
| `1`  | Studenten-WG |
| `4`  | Business-WG |
| `5`  | Wohnheim (dorm) |
| `6`  | Berufstätigen-WG |
| `7`  | Azubi-WG |
| `9`  | WG mit Kindern |
| `16` | LGBTQIA+ |
| `19` | Internationals welcome |
| `23` | keine Angaben zum Geschlecht |

**`src/crawler.py`** — how to extract the type code from a listing card:

```python
type_el = card.locator("[data-filter-value]").first
wg_type_code = type_el.get_attribute("data-filter-value") if type_el.count() else ""
```

Each card has a hidden badge with `data-filter-value="2"` (or whichever code). Single apartments have no such element → `wg_type_code` is `""`.

Also injected into the search URL:

```python
for ftype in WG_FLATSHARE_TYPES:
    param_list.append(("flatshare_types[]", ftype))
```

**`src/filters.py`** — the Python check:

```python
def _wg_type_ok(wg_type_code: str) -> bool:
    if not WG_FLATSHARE_TYPES or not wg_type_code:
        return True  # no filter set, or listing has no type (e.g. single apartment) → pass
    return wg_type_code in WG_FLATSHARE_TYPES
```

> **Key behaviour:** single apartments (`categories[]=1` or `2`) have no `wg_type_code`, so they always pass the type filter regardless of `WG_FLATSHARE_TYPES`. To exclude single apartments entirely, remove them from the search URL categories instead.

---

## Summary — what to implement

| What | Where | How |
|------|-------|-----|
| WG room vs. apartment | `SEARCH_URL` in `config.py` | `categories[]` query params |
| WG size cap | `config.py` + `filters.py` + `crawler.py` | `WG_SIZE_MAX`, regex on location, `wg_flatmates_to` URL param |
| WG gender/type | `config.py` + `filters.py` + `crawler.py` | `WG_FLATSHARE_TYPES`, `data-filter-value` attribute, `flatshare_types[]` URL param |
