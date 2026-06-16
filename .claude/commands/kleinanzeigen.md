# Kleinanzeigen Hamburg Apartment Scanner

Search Kleinanzeigen for Hamburg rental apartments matching the user's criteria, filter them, analyze with AI, and send Telegram notifications for matches. You are acting as an automated apartment scout.

## Step 1 — Load preferences

Read `/Users/philipp/Documents/Repos/wggesucht/config.toml` and extract:
- `max_rent` → integer
- `move_in_from` → date string (YYYY-MM-DD)
- `stay_until` → date string (YYYY-MM-DD)
- `preferred` districts → list of strings (all lowercase)
- `profile.context`, `profile.must_haves`, `profile.strong_preferences`

Read `/Users/philipp/Documents/Repos/wggesucht/data/seen_kleinanzeigen.json`.
If it doesn't exist, treat seen IDs as an empty list `[]`.

## Step 2 — Fetch listings (2 pages)

Fetch both pages newest-first. Replace MAX_RENT with the value from config:

Page 1: `https://www.kleinanzeigen.de/s-wohnung-mieten/hamburg/preis::MAX_RENT/c203l9409?sortingField=SORTING_DATE`
Page 2: `https://www.kleinanzeigen.de/s-wohnung-mieten/hamburg/preis::MAX_RENT/c203l9409/seite:2?sortingField=SORTING_DATE`

For each listing card extract:
- **Title**
- **Price** (€/month — skip if clearly a total/deposit, not monthly rent)
- **Location** (e.g. "Hamburg · Alsterdorf")
- **Relative URL** (e.g. `/s-anzeige/title-123456789.html`)
- **Listing ID** — the last number before `.html` in the URL
- **Date posted**

If WebFetch is blocked or returns no listing cards, fall back to WebSearch:
`site:kleinanzeigen.de wohnung mieten hamburg möbliert zwischenmiete untermiete`
Extract listing URLs from the search results and continue.

## Step 3 — Hard filters (fast, no detail page needed)

For each listing, run these checks in order. Skip to the next listing on first failure.

1. **Already seen**: if listing ID is in seen_kleinanzeigen.json → skip silently
2. **Price**: price must be ≤ max_rent. If no price shown → pass through (unknown)
3. **District**: location must contain at least one district from the preferred list loaded in Step 1 (case-insensitive match). If location is just "Hamburg" with no sub-district → pass through

Listings that pass all three: fetch their detail page for full description text.

## Step 4 — Detail page filters (after fetching full listing)

Fetch each passing listing's full page: `https://www.kleinanzeigen.de` + relative URL

From the full listing text, apply these additional filters:

4. **End date**: if the listing explicitly states an end/move-out date AND that date is before `stay_until` from config → reject. If no end date mentioned → pass.
5. **Scam pre-check**: if listing asks to contact via WhatsApp only, requests upfront payment, or has no Hamburg address at all → reject immediately, do not notify.

## Step 5 — AI analysis

For each listing that passed all filters, analyze the full listing text:

**You are evaluating this for:** someone doing a 5-month internship at Lufthansa Technik Hamburg (near Airport/Fuhlsbüttel) starting September 2026, needing a furnished sublet from August 2026 through February 2027. Short commute to Fuhlsbüttel is important. They have no furniture so furnished is a must-have.

Produce:
- **scam_score** (1–10): 1 = totally safe, 10 = obvious scam
- **recommendation_score** (1–10): 1 = terrible fit, 10 = perfect
- **pros**: 2–3 bullet points
- **cons**: 2–3 bullet points
- **summary**: one short keyword line (e.g. "Furnished · Eppendorf · Aug–Jan · good commute")
- **dates_ok**: true/false — does the availability window cover Aug 2026–Feb 2027?

Only send a notification if `recommendation_score ≥ 4` and `scam_score ≤ 3`.

## Step 6 — Send Telegram notification

For each listing that passes the score threshold, send a Telegram message using Python (handles special characters safely):

```bash
/Users/philipp/Documents/Repos/wggesucht/venv/bin/python3 -c "
import urllib.request, urllib.parse, json

msg = '''MESSAGE_HERE'''

data = urllib.parse.urlencode({
    'chat_id': '6340047322',
    'parse_mode': 'HTML',
    'text': msg,
}).encode()
resp = urllib.request.urlopen(
    'https://api.telegram.org/bot8795430494:AAHN4ubNVcu_ulc5xjfz9OrESe00oJrmR84/sendMessage',
    data
)
print(json.loads(resp.read())['ok'])
"
```

Message format (substitute values, keep the HTML tags):
```
🏠 <b>TITLE</b>
💶 PRICE €  ·  📅 DATES_OR_N/A
📍 LOCATION

⭐ Match: SCORE/10  ·  🚨 Scam: SCAM_SCORE/10
<i>SUMMARY</i>

✅ PRO_1
✅ PRO_2

⚠️ CON_1
⚠️ CON_2

🔗 https://www.kleinanzeigen.de/s-anzeige/LISTING_PATH
```

## Step 7 — Update seen IDs

After processing all listings (whether they matched or not), write ALL fetched IDs back to the seen file so they are skipped next run:

```bash
/Users/philipp/Documents/Repos/wggesucht/venv/bin/python3 -c "
import json, sys
from pathlib import Path

path = Path('/Users/philipp/Documents/Repos/wggesucht/data/seen_kleinanzeigen.json')
existing = json.loads(path.read_text()) if path.exists() else []
new_ids = sys.argv[1:]
merged = list(set(existing + new_ids))
path.write_text(json.dumps(merged))
print(f'Saved {len(merged)} seen IDs ({len(new_ids)} new)')
" ID1 ID2 ID3
```

Replace `ID1 ID2 ID3` with the actual listing IDs collected in Step 2, space-separated.

## Step 8 — Report

Print a one-line summary:
`Kleinanzeigen: X listings found · Y new · Z passed filters · N notifications sent`
