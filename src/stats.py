import json
from datetime import datetime, timedelta

from src.config import DATA_DIR

STATS_FILE = DATA_DIR / "stats.json"


def record_run(
    *,
    listings_scraped: int,
    new_listings: int,
    matches: int,
    relogged: bool,
    errors: list[str],
    ai_calls: int,
) -> None:
    entry = {
        "ts": datetime.now().isoformat(),
        "scraped": listings_scraped,
        "new": new_listings,
        "matches": matches,
        "relogged": relogged,
        "errors": errors,
        "ai_calls": ai_calls,
    }
    records: list[dict] = []
    if STATS_FILE.exists():
        try:
            records = json.loads(STATS_FILE.read_text())
        except Exception:
            pass
    records.append(entry)
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATS_FILE.write_text(json.dumps(records, indent=2))


def load_since(hours: int = 24) -> list[dict]:
    if not STATS_FILE.exists():
        return []
    try:
        records: list[dict] = json.loads(STATS_FILE.read_text())
    except Exception:
        return []
    cutoff = datetime.now() - timedelta(hours=hours)
    return [r for r in records if datetime.fromisoformat(r["ts"]) >= cutoff]
