"""Phase 1 research tool — verifies the WG-Gesucht contact-form selectors on a real
listing page WITHOUT ever submitting anything. Run manually against a few real URLs:

    venv/bin/python3 scripts/inspect_contact_form.py <listing_url>
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv()

from src.browser import authenticated_page

_NAME_SELECTOR = "div.user_profile_info p.mb0"
_MEMBER_SINCE_RE = "Mitglied seit"

_CONTACT_BUTTON_SELECTOR = "a.wgg-btn:has-text('Nachricht senden')"


def _dismiss_cookie_banner(page):
    try:
        page.click("a.cmptxt_btn_yes", timeout=3000)
        page.wait_for_timeout(800)
    except Exception:
        pass


def _first_visible(locator):
    """Return the first visible match among all matches (site duplicates elements
    per responsive breakpoint — most are display:none at any given viewport)."""
    for i in range(locator.count()):
        el = locator.nth(i)
        if el.is_visible():
            return el
    return None


def inspect(url: str) -> None:
    print(f"\n=== {url} ===")
    with authenticated_page(headless=True) as page:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        _dismiss_cookie_banner(page)

        name = None
        for i in range(page.locator(_NAME_SELECTOR).count()):
            el = page.locator(_NAME_SELECTOR).nth(i)
            if not el.is_visible():
                continue
            text = el.inner_text().strip()
            if text and _MEMBER_SINCE_RE not in text:
                name = text
                break
        if name:
            print(f"  NAME  ok  selector={_NAME_SELECTOR!r}  value={name!r}")
        else:
            print(f"  NAME  not present for this listing (owner has no public name — will use fallback salutation)")

        btn = _first_visible(page.locator(_CONTACT_BUTTON_SELECTOR))
        if btn:
            print(f"  BUTTON  ok  selector={_CONTACT_BUTTON_SELECTOR!r}")
            btn.click()
            page.wait_for_timeout(1500)
        else:
            print(f"  BUTTON  NOT FOUND — selector={_CONTACT_BUTTON_SELECTOR!r}")
            return

        print(f"  URL after click: {page.url}")

        try:
            ta = _first_visible(page.locator("#message_input"))
            print(f"  TEXTAREA #message_input  found={ta is not None}")
        except Exception as e:
            print(f"  TEXTAREA check failed: {e}")

        try:
            submit = _first_visible(page.locator("button.conversation_send_button, button.create_new_conversation"))
            print(f"  SUBMIT button  found={submit is not None}")
        except Exception as e:
            print(f"  SUBMIT check failed: {e}")

        print("  Done — NOTHING was submitted.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: inspect_contact_form.py <listing_url> [<listing_url> ...]")
    for u in sys.argv[1:]:
        inspect(u)
