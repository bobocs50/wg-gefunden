#!/usr/bin/env python3
"""
Daily heartbeat — run via cron at 07:00 to confirm the bot is alive and summarise the last 24h.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from datetime import datetime
from src.stats import load_since
from src.config import SEEN_IDS_FILE, SESSION_FILE
import src.telegram as telegram


def _seen_count() -> int:
    if not SEEN_IDS_FILE.exists():
        return 0
    try:
        return len(json.loads(SEEN_IDS_FILE.read_text()))
    except Exception:
        return 0


def _session_age() -> str:
    if not SESSION_FILE.exists():
        return "missing"
    age_h = (datetime.now().timestamp() - SESSION_FILE.stat().st_mtime) / 3600
    if age_h < 1:
        return f"{int(age_h * 60)}m old"
    if age_h < 48:
        return f"{int(age_h)}h old"
    return f"{int(age_h / 24)}d old — may need refresh"


runs = load_since(hours=24)
now = datetime.now().strftime("%d.%m.%Y %H:%M")

if not runs:
    telegram.send(
        f"⚠️ <b>WG-Gesucht — daily report</b>\n"
        f"🕐 {now}\n\n"
        f"No runs recorded in the last 24h — cron may be broken."
    )
    sys.exit(0)

total_runs     = len(runs)
total_scraped  = sum(r["scraped"] for r in runs)
total_new      = sum(r.get("new", 0) for r in runs)
total_matches  = sum(r["matches"] for r in runs)
total_relogins = sum(1 for r in runs if r["relogged"])
total_ai       = sum(r["ai_calls"] for r in runs)
all_errors     = [e for r in runs for e in r["errors"]]

stats_lines = [
    f"Runs:         {total_runs}",
    f"Scraped:      {total_scraped} listings",
    f"New (unseen): {total_new}",
    f"Matches:      {total_matches}",
    f"AI calls:     {total_ai}",
    f"",
    f"Relogins:     {total_relogins}",
    f"Errors:       {len(all_errors)}",
]
if all_errors:
    for e in list(dict.fromkeys(all_errors))[:3]:
        stats_lines.append(f"  • {e}")
stats_lines += [
    f"",
    f"Seen total:   {_seen_count():,} listings",
    f"Session:      {_session_age()}",
]

msg = (
    f"📊 <b>WG-Gesucht — daily report</b>\n"
    f"🕐 {now}\n\n"
    f"<pre>{chr(10).join(stats_lines)}</pre>"
)

if total_matches == 0:
    msg += "\n\n<i>No matches today — filters may be too strict.</i>"

telegram.send(msg)
