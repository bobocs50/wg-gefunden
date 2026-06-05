import json
import os
import time
import urllib.request

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def _send_once(text: str) -> bool:
    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except urllib.error.HTTPError as e:
        print(f"Telegram error {e.code}: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def send(text: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        print("WARNING: Telegram not configured — skipping notification")
        return False
    if _send_once(text):
        return True
    print("WARNING: Telegram send failed — retrying in 3s...")
    time.sleep(3)
    if _send_once(text):
        return True
    print("WARNING: Telegram send failed after retry — message dropped")
    return False


def _listing_header(listing: dict) -> str:
    return f"🏠 <b>{listing.get('title', '?')}</b>"


def format_listing(listing: dict) -> str:
    url = listing.get("url", "")
    return (
        f"{_listing_header(listing)}\n"
        f"💶 {listing.get('price_text', '?')}\n"
        f"📍 {listing.get('location', '?')}\n"
        f"📅 {listing.get('date_text', '?')}\n"
        f"🔗 <a href=\"{url}\">{url}</a>"
    )


def format_listing_with_ai(listing: dict, analysis: dict) -> str:
    url = listing.get("url", "")
    match = analysis.get("recommendation_score", "?")
    scam = analysis.get("scam_score", "?")
    scam_reason = analysis.get("scam_reason", "")

    pros = "\n".join(f"✅ {p}" for p in analysis.get("pros", [])[:3]) or "✅ —"
    cons = "\n".join(f"⚠️ {c}" for c in analysis.get("cons", [])[:3]) or "⚠️ —"
    summary = analysis.get("summary", "")

    location = listing.get('location', '?')
    location_parts = [p.strip() for p in location.split("|")]
    location_short = " · ".join(location_parts[1:]) if len(location_parts) > 1 else location

    scam_line = f"<i>{scam_reason}</i>\n" if scam_reason else ""
    summary_line = f"\n💬 <i>{summary}</i>\n" if summary else ""

    return (
        f"{_listing_header(listing)}\n"
        f"💶 {listing.get('price_text', '?')}  ·  📅 {listing.get('date_text', '?')}\n"
        f"📍 {location_short}\n"
        f"\n"
        f"⭐ Match: <b>{match}/10</b>  ·  🚨 Scam: <b>{scam}/10</b>\n"
        f"{scam_line}"
        f"\n"
        f"{pros}\n"
        f"\n"
        f"{cons}\n"
        f"{summary_line}"
        f"\n"
        f"🔗 <a href=\"{url}\">{url}</a>"
    )
