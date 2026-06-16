# Kleinanzeigen Hamburg Apartment Scanner

Search Kleinanzeigen for Hamburg rental apartments matching the user's criteria, filter them, analyze with AI, and send Telegram notifications for matches.

## Step 1 — Load preferences

Read `/Users/philipp/Documents/Repos/wggesucht/config.toml` and extract:
- `max_rent` (search.max_rent)
- `move_in_from` and `move_in_to` (search.move_in_from / move_in_to)
- `stay_until` (search.stay_until)
- `preferred` districts (districts.preferred)
- Profile context (profile.context, profile.must_haves)

Read `/Users/philipp/Documents/Repos/wggesucht/data/seen_kleinanzeigen.json` if it exists (list of already-notified listing IDs). If the file doesn't exist, treat seen IDs as empty list.

## Step 2 — Fetch listings

Fetch this URL (replace MAX_RENT with the value from config):
`https://www.kleinanzeigen.de/s-wohnung-mieten/hamburg/preis-bis-MAX_RENT/c203l9409`

Parse the HTML to extract listings. For each listing card look for:
- Title
- Price (€/month)
- Location/district
- URL (e.g. `/s-anzeige/...`)
- Listing ID (the number in the URL)
- Date posted

If WebFetch is blocked or returns no listings, try WebSearch with query:
`site:kleinanzeigen.de wohnung mieten hamburg möbliert zwischenmiete untermiete`

## Step 3 — Filter

Skip listings whose ID is already in seen_kleinanzeigen.json.

For each new listing apply these hard filters — note which ones fail:
- **Price**: must be ≤ max_rent
- **District**: location must contain one of the preferred districts (case-insensitive). Preferred: winterhude, alsterdorf, eppendorf, gross borstel, fuhlsbüttel, ohlsdorf, harvestehude, hoheluft, lokstedt, eimsbüttel, barmbek-nord, barmbek-süd, niendorf, langenhorn, hummelsbüttel, wellingsbüttel, poppenbüttel
- **Not already seen**

If a listing passes price and district, fetch its detail page to get the full description.

## Step 4 — Analyze each match

For each listing that passed the hard filters, analyze the full listing text and answer:

**Scam score** (1–10): red flags like "send money first", vague contact, too-good price
**Recommendation score** (1–10): how well it fits someone doing a 5-month internship at Lufthansa Technik Hamburg (near Airport/Fuhlsbüttel) starting September 2026, needing a furnished sublet from August 2026 through February 2027
**Pros**: 2–3 bullet points
**Cons**: 2–3 bullet points  
**Summary**: one short keyword line (e.g. "Furnished · Eppendorf · Sept–Jan")
**Available**: does the listing seem available for the needed period (Aug 2026 – Feb 2027)? If dates are mentioned and they don't cover this window, note it.

## Step 5 — Send Telegram notification

For each analyzed match, send a Telegram message via curl:

```bash
curl -s -X POST "https://api.telegram.org/bot8795430494:AAHN4ubNVcu_ulc5xjfz9OrESe00oJrmR84/sendMessage" \
  -d chat_id=6340047322 \
  -d parse_mode=HTML \
  -d text="MESSAGE"
```

Format (HTML):
```
🏠 <b>TITLE</b>
💶 PRICE €  ·  📅 DATES_OR_UNKNOWN
📍 DISTRICT

⭐ Match: SCORE/10  ·  🚨 Scam: SCAM_SCORE/10
<i>SUMMARY_LINE</i>

✅ PRO 1
✅ PRO 2

⚠️ CON 1
⚠️ CON 2

🔗 https://www.kleinanzeigen.de/s-anzeige/LISTING_PATH
```

## Step 6 — Update seen IDs

After processing all listings (matched or not), append ALL fetched listing IDs to `data/seen_kleinanzeigen.json` using Bash, so they are skipped on the next run.

```bash
# Read existing, merge new IDs, write back
```

## Step 7 — Report

Print a summary: how many listings were found, how many were new, how many passed filters, how many notifications were sent.
