import json
import os
import urllib.request

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send(text: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        print("WARNING: Telegram not configured — skipping notification")
        return False

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

    pros_line = " · ".join(analysis.get("pros", [])) or "—"
    cons_line = " · ".join(analysis.get("cons", [])) or "—"
    summary = analysis.get("summary", "")

    return (
        f"{_listing_header(listing)}\n"
        f"💶 {listing.get('price_text', '?')} · 📍 {listing.get('location', '?')} · 📅 {listing.get('date_text', '?')}\n"
        f"\n"
        f"⭐ Match: {match}/10   🚨 Scam risk: {scam}/10\n"
        f"<i>{scam_reason}</i>\n"
        f"\n"
        f"✅ <b>Pros:</b> {pros_line}\n"
        f"⚠️ <b>Cons:</b> {cons_line}\n"
        f"\n"
        f"💬 <b>Summary:</b> <i>{summary}</i>\n"
        f"\n"
        f"🔗 <a href=\"{url}\">{url}</a>"
    )
