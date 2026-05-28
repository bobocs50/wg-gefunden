"""One-shot manual login — only needed to create the initial session.json.
After that, main.py re-logins automatically when the session expires."""
from dotenv import load_dotenv
load_dotenv()

from playwright.sync_api import sync_playwright
from src.auth import login


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        success = login(page, context)
        browser.close()
        if not success:
            raise SystemExit("Login failed — check WGG_EMAIL / WGG_PASSWORD in .env")
    print("Done.")


if __name__ == "__main__":
    main()
