import os

from playwright.sync_api import Page, BrowserContext

from src.config import SESSION_FILE

WGG_HOME = "https://www.wg-gesucht.de"


def is_logged_in(page: Page) -> bool:
    """A logout link only exists in the nav when a user is logged in."""
    return page.locator("a[href*='logout']").count() > 0


def login(page: Page, context: BrowserContext) -> bool:
    """Log in using WGG_EMAIL / WGG_PASSWORD from .env and persist the session.

    Returns True on success, False if credentials are missing or login fails.
    """
    email = os.getenv("WGG_EMAIL", "")
    password = os.getenv("WGG_PASSWORD", "")
    if not email or not password:
        print("WARNING: WGG_EMAIL / WGG_PASSWORD not set — cannot auto-login")
        return False

    print("Session expired — logging in automatically...")
    page.goto(WGG_HOME, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    # Dismiss cookie banner if present
    try:
        page.wait_for_selector("a.cmptxt_btn_yes", timeout=4000)
        page.click("a.cmptxt_btn_yes")
        page.wait_for_timeout(1000)
    except Exception:
        pass

    # Open login dropdown
    try:
        page.click(".dropdown-mini > a", timeout=5000)
        page.wait_for_timeout(1500)
    except Exception as e:
        print(f"WARNING: Could not open login dropdown: {e}")
        return False

    # Fill email
    for sel in ["input#login_email_username", "input[name='login_email_username']", "input[type='email']"]:
        try:
            page.wait_for_selector(sel, state="visible", timeout=3000)
            page.fill(sel, email)
            break
        except Exception:
            continue

    # Fill password
    for sel in ["input#login_password", "input[name='login_password']", "input[type='password']"]:
        try:
            page.wait_for_selector(sel, state="visible", timeout=3000)
            page.fill(sel, password)
            break
        except Exception:
            continue

    # Submit
    try:
        page.locator("input#login_submit").click(force=True, timeout=5000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"WARNING: Login submit failed: {e}")
        return False

    context.storage_state(path=str(SESSION_FILE))
    print(f"Session saved → {SESSION_FILE}")
    return True
