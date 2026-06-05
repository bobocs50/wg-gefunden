from contextlib import contextmanager
from typing import Generator

from playwright.sync_api import sync_playwright, BrowserContext, Page

from src.config import SESSION_FILE

_LAUNCH_ARGS = ["--no-sandbox", "--disable-setuid-sandbox"]


@contextmanager
def authenticated_page(headless: bool = True) -> Generator[Page, None, None]:
    """Context manager that yields a Page with the saved session loaded (if it exists)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=_LAUNCH_ARGS)
        try:
            if SESSION_FILE.exists():
                context = browser.new_context(storage_state=str(SESSION_FILE))
            else:
                print("WARNING: No session file — running without login")
                context = browser.new_context()
            page = context.new_page()
            page.set_viewport_size({"width": 1280, "height": 900})
            yield page
        finally:
            browser.close()


@contextmanager
def fresh_page(headless: bool = True) -> Generator[tuple[Page, BrowserContext], None, None]:
    """Context manager that yields (Page, BrowserContext) with no session loaded.

    The BrowserContext is exposed so callers can persist the session after login
    via context.storage_state().
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=_LAUNCH_ARGS)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.set_viewport_size({"width": 1280, "height": 900})
            yield page, context
        finally:
            browser.close()
