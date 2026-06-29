import os
import unittest
from unittest.mock import patch

import main
from src.listing import Listing


def make_listing(**kwargs) -> Listing:
    defaults = dict(
        id="smoke-1",
        title="Nice flat in Winterhude",
        price_text="950 €",
        location="Hamburg | Winterhude",
        date_text="01.08.2026 - 01.02.2027",
        date_start="01.08.2026",
        date_end="01.02.2027",
        last_online="01.06.2026",
        url="https://wg-gesucht.de/angebote/smoke-1",
        wg_type_code="",
    )
    defaults.update(kwargs)
    return Listing(**defaults)


class TestMainSmoke(unittest.TestCase):
    def test_main_success_pipeline_smoke(self):
        listing = make_listing()

        with (
            patch.dict(
                os.environ,
                {"TELEGRAM_BOT_TOKEN": "token", "TELEGRAM_CHAT_ID": "chat"},
                clear=False,
            ),
            patch.object(main, "AI_ENABLED", False),
            patch("main.ensure_session", return_value=(True, False)),
            patch("main.load_seen", return_value=set()),
            patch("main.crawl", return_value=[listing]),
            patch("main.save_seen") as save_seen,
            patch("main.record_run") as record_run,
            patch("src.pipeline.AI_ENABLED", False),
            patch("src.pipeline.run_checks", return_value=[("smoke", "ok", True)]),
            patch("src.pipeline.format_listing", return_value="listing-msg"),
            patch("src.pipeline.send") as send_pipeline,
        ):
            main.main()

        save_seen.assert_called_once_with({"smoke-1"})
        send_pipeline.assert_called_once_with("listing-msg")
        record_run.assert_called_once_with(
            listings_scraped=1,
            new_listings=1,
            matches=1,
            relogged=False,
            errors=[],
            ai_calls=0,
        )

    def test_main_session_failure_smoke(self):
        with (
            patch.dict(
                os.environ,
                {"TELEGRAM_BOT_TOKEN": "token", "TELEGRAM_CHAT_ID": "chat"},
                clear=False,
            ),
            patch.object(main, "AI_ENABLED", False),
            patch("main.ensure_session", return_value=(False, True)),
            patch("main.crawl") as crawl,
            patch("main.record_run") as record_run,
            patch("main.send") as send,
        ):
            main.main()

        crawl.assert_not_called()
        record_run.assert_called_once_with(
            listings_scraped=0,
            new_listings=0,
            matches=0,
            relogged=True,
            errors=["session_failed"],
            ai_calls=0,
        )
        self.assertEqual(send.call_count, 1)
        self.assertIn("login failed", send.call_args.args[0].lower())


if __name__ == "__main__":
    unittest.main()
