# AI Apartment Hunter – WG-Gesucht + Kleinanzeigen

## Goal

Crawl Hamburg rental listings, filter them automatically, and send a Telegram notification with an AI-written summary for any good match.

## Target

* Single apartment / studio
* Hamburg
* Preferred districts: Eppendorf, Fuhlsbüttel, Ohlsdorf, Alsterdorf, Barmbek-Nord, Winterhude
* Rental period: mid August → early February
* Prefer: furnished, temporary sublet, Zwischenmiete
* Budget: configurable

## Sources

* https://www.wg-gesucht.de

---

## Tech Stack

```
Python 3.12
playwright              # browser automation + session persistence
anthropic / openai      # AI-written summary per listing
python-telegram-bot     # push notifications
json file               # track seen listing IDs
```

No database, no Docker, no PM2, no VPS required.

---

## How It Works

1. **Crawl** — Playwright logs in once, saves session to disk, reuses it on every run
2. **Filter** — hard filters applied locally (no AI needed):
   - City: Hamburg only
   - District: matches preferred list
   - Duration: overlaps with Aug–Feb window
   - Price: within configured budget
3. **AI summary** — for listings that pass filters, call Claude/OpenAI to write a short summary (price, pros, scam check, fit score)
4. **Telegram push** — send formatted message with title, district, price, AI summary, and direct URL

Only new listings are processed. Seen IDs stored in a local JSON file.

---

## Notification Format

```
🏠 [Title]
📍 District | 💶 Price/month
📅 Available: [dates]
⭐ AI Score: 8/10

[2-3 sentence AI summary]

🔗 [Direct URL]
```

---

## Filters

**Hard (must pass):**
- Hamburg only
- Rental period overlaps Aug 15 – Feb 5
- Price ≤ budget
- Not a roommate-only offer

**Soft (used by AI):**
- Preferred district
- Furnished
- Legitimate-sounding listing
- No scam signals

---

## Running It

* **Local Mac** — cron job every 10–15 min, Mac stays on
* **Cloud** — Railway or Render (always-on, free tier, supports headless Chromium)

---

## Project Structure

```
/src
  crawler.py       # Playwright scraping + session
  filters.py       # hard filter logic
  ai.py            # Claude/OpenAI summary call
  telegram.py      # send notification
  seen.py          # read/write seen IDs JSON

/data
  seen_ids.json
  session.json     # Playwright storage state

.env               # API keys, Telegram token, budget
main.py            # entry point
```

---

## MVP Phases

**v1** — crawl + filter + Telegram alert (no AI)
**v2** — add AI summary + scam detection
**v3** — auto-draft application messages (human approval before send)
