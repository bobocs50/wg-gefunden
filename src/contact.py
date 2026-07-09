from src.browser import authenticated_page

_NAME_SELECTOR = "div.user_profile_info p.mb0"
_MEMBER_SINCE_MARKER = "Mitglied seit"


def _dismiss_cookie_banner(page):
    try:
        page.click("a.cmptxt_btn_yes", timeout=3000)
        page.wait_for_timeout(800)
    except Exception:
        pass


def extract_owner_name(url: str) -> str | None:
    """Best-effort extraction of the listing owner's public display name.

    Returns None if the owner has no public name shown (common — many profiles
    only show a join date), or if extraction fails for any reason.
    """
    try:
        with authenticated_page(headless=True) as page:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)
            _dismiss_cookie_banner(page)

            locator = page.locator(_NAME_SELECTOR)
            for i in range(locator.count()):
                el = locator.nth(i)
                if not el.is_visible():
                    continue
                text = el.inner_text().strip()
                if text and _MEMBER_SINCE_MARKER not in text:
                    return text
            return None
    except Exception as e:
        print(f"extract_owner_name failed ({e}) — {url}")
        return None
