import json
import os

from src.config import SEEN_IDS_FILE


def load_seen() -> set[str]:
    if not SEEN_IDS_FILE.exists():
        return set()
    return set(json.loads(SEEN_IDS_FILE.read_text()))


def save_seen(ids: set[str]) -> None:
    SEEN_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SEEN_IDS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(sorted(ids), indent=2))
    os.replace(tmp, SEEN_IDS_FILE)
