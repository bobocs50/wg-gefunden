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


def format_listing(listing: dict) -> str:
    url = listing.get("url", "")
    return (
        f"🏠 <b>{listing.get('title', '?')}</b>\n"
        f"💶 {listing.get('price_text', '?')}\n"
        f"📍 {listing.get('location', '?')}\n"
        f"📅 {listing.get('date_text', '?')}\n"
        f"🔗 <a href=\"{url}\">{url}</a>"
    )
