"""
Last-resort crash reporter.

Installs a ``sys.excepthook`` that pipes any unhandled exception — including
``ImportError`` raised while the entry-point module is still being imported —
to Telegram. Both ``main.py`` and ``scripts/heartbeat.py`` wire this up
*before* importing ``src.config``, so a missing ``config.toml`` on the server
alerts the operator instead of dying in the cron log.

Nothing in this module may import ``src.config``. That is the whole point.
"""
import html
import sys
import traceback
from typing import Callable

_MAX_TRACEBACK_CHARS = 1500


def _default_send(text: str) -> None:
    # Imported lazily so this module has no import-time cost and no coupling
    # to src.config (src.telegram only depends on src.listing, a pure dataclass).
    from src.telegram import send
    send(text)


def format_alert(entry_point: str, exc_type: type, exc_value: BaseException, tb) -> str:
    trace = "".join(traceback.format_exception(exc_type, exc_value, tb))
    tail = trace[-_MAX_TRACEBACK_CHARS:]
    # Also cap the one-line summary — Telegram messages are limited to 4096 chars
    # and a giant exc_value (e.g. a huge string in a ValueError) would blow past it.
    summary = f"{exc_type.__name__}: {exc_value}"
    if len(summary) > 200:
        summary = summary[:200] + "…"
    # Telegram uses HTML parse mode: escape entities in user-controlled strings.
    # Python tracebacks contain "<module>" as a frame name, which Telegram would
    # otherwise reject as an unknown tag ("Bad Request: Unsupported start tag").
    return (
        f"🚨 <b>WG-Gesucht bot crashed</b>\n"
        f"entry: <code>{html.escape(entry_point)}</code>\n"
        f"error: <code>{html.escape(summary)}</code>\n\n"
        f"<pre>{html.escape(tail)}</pre>"
    )


def install_excepthook(
    entry_point: str,
    send: Callable[[str], None] = _default_send,
) -> Callable:
    """Install a top-level excepthook that alerts Telegram on any uncaught error.

    Returns the previous excepthook so callers can restore it (used by tests).
    ``SystemExit`` and ``KeyboardInterrupt`` are passed through unchanged — those
    are intentional shutdowns, not crashes.
    """
    previous = sys.excepthook

    def hook(exc_type, exc_value, tb):
        if issubclass(exc_type, (SystemExit, KeyboardInterrupt)):
            previous(exc_type, exc_value, tb)
            return
        try:
            send(format_alert(entry_point, exc_type, exc_value, tb))
        except Exception as alert_err:
            # Never let the alerter itself hide the original traceback.
            print(f"crash_alert: failed to send Telegram alert: {alert_err}", file=sys.stderr)
        previous(exc_type, exc_value, tb)

    sys.excepthook = hook
    return previous
