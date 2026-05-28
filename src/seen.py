import json

from src.config import SEEN_IDS_FILE


def load_seen() -> set[str]:
    if not SEEN_IDS_FILE.exists():
        return set()
    return set(json.loads(SEEN_IDS_FILE.read_text()))


def save_seen(ids: set[str]) -> None:
    SEEN_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_IDS_FILE.write_text(json.dumps(sorted(ids), indent=2))


def mark_seen(existing: set[str], new_ids: list[str]) -> set[str]:
    existing.update(new_ids)
    save_seen(existing)
    return existing
