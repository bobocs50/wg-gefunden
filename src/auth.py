import os

from playwright.sync_api import sync_playwright

from src.config import SESSION_FILE

WGG_HOME = "https://www.wg-gesucht.de"


def _session_valid() -> bool:
    """Check whether the saved session is still authenticated."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(storage_state=str(SESSION_FILE))
            page = context.new_page()
            page.goto(WGG_HOME, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            # Logged-in users see their inbox/profile links; the login submit button is absent
            return page.locator("input#login_submit").count() == 0
        finally:
            browser.close()


def _do_login() -> bool:
    """Log in headlessly, save session. Returns True on success."""
    email = os.getenv("WGG_EMAIL", "")
    password = os.getenv("WGG_PASSWORD", "")
    if not email or not password:
        print("WARNING: WGG_EMAIL / WGG_PASSWORD not set — cannot auto-login")
        return False

    print("Logging in to WG-Gesucht...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(WGG_HOME, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # Dismiss cookie banner if present
            try:
                page.wait_for_selector("a.cmptxt_btn_yes", timeout=4000)
                page.click("a.cmptxt_btn_yes")
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(1500)
            except Exception:
                pass

            # Fill and submit the login form via JS (form is in DOM but hidden inside dropdown)
            try:
                page.wait_for_selector("input#login_email_username", state="attached", timeout=10000)
                page.evaluate(f"""
                    const e = document.querySelector('input#login_email_username');
                    const p = document.querySelector('input#login_password');
                    e.value = {repr(email)};
                    e.dispatchEvent(new Event('input', {{bubbles: true}}));
                    p.value = {repr(password)};
                    p.dispatchEvent(new Event('input', {{bubbles: true}}));
                    document.querySelector('input#login_submit').click();
                """)
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"WARNING: Login failed: {e}")
                return False

            # Consider login successful if we're no longer on the login page
            if page.locator("input#login_submit").count() > 0:
                print("WARNING: Login failed — still on login page (wrong credentials?)")
                return False

            SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(SESSION_FILE))
            print(f"Session saved → {SESSION_FILE}")
            return True
        finally:
            browser.close()


def ensure_session() -> bool:
    """Ensure a valid session file exists before crawling. Re-logins automatically if expired."""
    if SESSION_FILE.exists() and _session_valid():
        print("Session valid.")
        return True
    print("Session missing or expired — re-logging in...")
    return _do_login()
