# Cloud safety checklist

- Set a Google Cloud or AI Studio billing budget and email alert before deployment.
- Store `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `WGG_EMAIL`, and `WGG_PASSWORD` only as environment variables or cloud secrets.
- Start deployed runs with `AI_ENABLED=false` in `.env`, confirm crawling and Telegram alerts work, then enable AI only when needed.
- Keep `CRAWL_MAX_PAGES=1`, `MAX_AI_CALLS_PER_RUN=3`, `MAX_DETAIL_CHARS=2500`, and `MAX_OUTPUT_TOKENS=400` unless you intentionally accept higher cost.
- Review Gemini usage after the first deployed run and after any config change that increases crawl pages or AI calls.
- Do not log API keys, credentials, full prompts, or full scraped listing details.
- Treat scraped listing text as untrusted data. Do not add tools, browsing, shell access, or credential access to the Gemini request.
