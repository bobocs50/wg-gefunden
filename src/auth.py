import os

from src.browser import authenticated_page, fresh_page
from src.config import SESSION_FILE

WGG_HOME = "https://www.wg-gesucht.de"


def _session_valid() -> bool:
    """Check whether the saved session is still authenticated."""
    with authenticated_page(headless=True) as page:
        page.goto(WGG_HOME, wait_until="domcontentloaded")
        page.wait_for_timeout(3500)
        # Dismiss cookie banner so it doesn't obscure the login button check
        try:
            page.click("a.cmptxt_btn_yes", timeout=3000)
            page.wait_for_timeout(1000)
        except Exception:
            pass
        # Logged-in users have the submit button hidden inside a dropdown (not visible)
        return not page.locator("input#login_submit").is_visible()


def _do_login() -> bool:
    """Log in headlessly, save session. Returns True on success."""
    email = os.getenv("WGG_EMAIL", "")
    password = os.getenv("WGG_PASSWORD", "")
    if not email or not password:
        print("WARNING: WGG_EMAIL / WGG_PASSWORD not set — cannot auto-login")
        return False

    print("Logging in to WG-Gesucht...")
    with fresh_page(headless=True) as (page, context):
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

        # Open the "Mein Konto" dropdown to make the login form visible
        try:
            page.locator("a:has-text('Mein Konto')").first.click()
            page.wait_for_selector("input#login_email_username", state="visible", timeout=5000)
        except Exception:
            pass

        # Fill and submit the login form
        try:
            page.wait_for_selector("input#login_email_username", state="visible", timeout=10000)
            page.fill("input#login_email_username", email)
            page.fill("input#login_password", password)
            page.click("input#login_submit")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"WARNING: Login failed: {e}")
            return False

        # Consider login successful if the submit button is no longer visible
        if page.locator("input#login_submit").is_visible():
            print("WARNING: Login failed — still on login page (wrong credentials?)")
            return False

        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(SESSION_FILE))
        print(f"Session saved → {SESSION_FILE}")
        return True


def ensure_session() -> tuple[bool, bool]:
    """Ensure a valid session file exists before crawling. Re-logins automatically if expired.

    Returns (ok, relogged): ok=False means the bot cannot run;
    relogged=True means a fresh login was performed (session had expired).
    """
    if SESSION_FILE.exists() and _session_valid():
        print("Session valid.")
        return True, False
    print("Session missing or expired — re-logging in...")
    ok = _do_login()
    return ok, ok
