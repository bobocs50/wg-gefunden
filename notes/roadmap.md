# Roadmap

## Setup

- [x] Init Python project (`requirements.txt`)
- [x] Configure `.env` (API keys, Telegram token, budget, filters)
- [x] Install dependencies (`pip install -r requirements.txt`)
- [x] Install Playwright Chromium (`playwright install chromium`)
- [x] Set up Telegram bot via BotFather

---

## v1 – Crawl + Filter + Alert

### Login
- [x] Run `login.py` — opens browser, logs into WG-Gesucht, saves `session.json`
- [x] Verify session saved to `data/session.json`

### WG-Gesucht Crawler
- [x] Load session on each run (skip login if valid)
- [x] Scrape listing cards from search results page
- [x] Extract: title, price, district, dates, URL, listing ID
- [x] Paginate through results

### Seen ID Tracking
- [x] Read `seen_ids.json` on startup
- [x] Skip already-seen listings
- [x] Write new IDs after processing

### Filters
- [x] Price ≤ budget
- [x] Rental period overlaps Aug–Feb
- [x] District matches preferred list

### Telegram Notifications
- [x] Send basic alert (title, price, district, URL)
- [x] Test end-to-end: crawl → filter → message received

### Scheduling
- [ ] Set up cron job (every 10–15 min)
- [ ] Test unattended runs

---

## v2 – AI Layer

- [ ] Integrate Gemini SDK
- [ ] Write evaluation prompt (score, scam check, pros/cons)
- [ ] Parse AI response reliably
- [ ] Add AI score + summary to Telegram message
- [ ] Scam warning if detected
- [ ] Only notify if score ≥ threshold (configurable)

---

## v3 – Application Drafts

- [ ] AI generates personalized application message per listing
- [ ] Draft stored locally for review
- [ ] Telegram message includes "approve to send" button
- [ ] On approval: send message to landlord (semi-automatic)

---

## Deployment – Hetzner VPS

- [ ] Rent Hetzner CX22 (~€3.79/mo)
- [ ] SSH in, install Python + Playwright + Chromium
- [ ] Upload code + `.env`
- [ ] Run `login.py` on server to generate session
- [ ] Set up cron job on server
- [ ] Monitor logs
