# Plan: Auto-Draft Application Message

## Progress
- [x] Phase 1: `draft_application()` Funktion + Prompt-Dateien
- [x] Phase 2: In `main.py` einbinden + 2. Telegram

---

## Phase 1: `draft_application()` Funktion + Prompt-Dateien
**Goal:** Neue Gemini-Funktion die das Template mit Listing-Details befüllt
**Effort:** ~1h

Steps:
1. `prompts/application_draft.md` anlegen — Gemini-Instruktion mit Platzhaltern `{{APPLICATION_TEMPLATE}}`, `{{LISTING}}`, `{{DETAIL_TEXT}}`
2. `src/config.py`: `APPLICATION_DRAFT_PROMPT_FILE` und `APPLICATION_TEMPLATE_FILE` hinzufügen
3. `src/ai.py`: `draft_application(listing, detail_text) -> str | None` hinzufügen
   - Lädt beide Prompt-Dateien (gecached)
   - Gemini-Call mit plain text output (kein JSON-Schema)
   - Bei Exception: `None` zurückgeben

**Risk:** Gemini-Response muss raw text sein, nicht JSON — anderer `response_mime_type` als `analyze()`

---

## Phase 2: In `main.py` einbinden + 2. Telegram
**Goal:** Nach der Analyse-Nachricht die Bewerbungsnachricht generieren und schicken
**Effort:** ~30min

Steps:
1. `draft_application` in `main.py` importieren
2. Nach `send(format_listing_with_ai(...))` und nach `send(format_listing(...))` (im AI-Branch): `draft_application()` aufrufen
3. Wenn Rückgabe nicht `None`: `telegram.send(draft)` aufrufen

**Risk:** Keiner — `details` dict ist an dieser Stelle bereits befüllt
