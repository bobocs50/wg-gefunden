import unittest
from unittest.mock import patch, MagicMock

from src.listing import Listing
import src.telegram as telegram_mod


def make_listing(**kwargs) -> Listing:
    defaults = dict(
        id="abc123",
        title="Schöne 1-Zimmer-Wohnung",
        price_text="750 €",
        location="Hamburg | Winterhude | Musterstraße",
        date_text="01.08.2026 - 31.01.2027",
        date_start="01.08.2026",
        date_end="31.01.2027",
        last_online="28.06.2026",
        url="https://www.wg-gesucht.de/abc123",
        wg_type_code="",
    )
    defaults.update(kwargs)
    return Listing(**defaults)


class TestFormatListing(unittest.TestCase):
    def setUp(self):
        self.listing = make_listing()
        self.text = telegram_mod.format_listing(self.listing)

    def test_contains_title(self):
        self.assertIn("Schöne 1-Zimmer-Wohnung", self.text)

    def test_contains_price(self):
        self.assertIn("750 €", self.text)

    def test_contains_location(self):
        self.assertIn("Hamburg | Winterhude", self.text)

    def test_contains_date(self):
        self.assertIn("01.08.2026 - 31.01.2027", self.text)

    def test_contains_url(self):
        self.assertIn("https://www.wg-gesucht.de/abc123", self.text)

    def test_is_string(self):
        self.assertIsInstance(self.text, str)

    def test_html_bold_on_title(self):
        self.assertIn("<b>", self.text)
        self.assertIn("</b>", self.text)

    def test_url_is_link(self):
        self.assertIn('<a href="', self.text)


class TestFormatListingWithAI(unittest.TestCase):
    def setUp(self):
        self.listing = make_listing()
        self.analysis = {
            "recommendation_score": 8,
            "scam_score": 2,
            "scam_reason": "",
            "pros": ["Close to airport", "Furnished", "Good price"],
            "cons": ["Small kitchen", "No balcony"],
            "summary": "Solid option for the internship period.",
        }
        self.text = telegram_mod.format_listing_with_ai(self.listing, self.analysis)

    def test_contains_title(self):
        self.assertIn("Schöne 1-Zimmer-Wohnung", self.text)

    def test_contains_recommendation_score(self):
        self.assertIn("8/10", self.text)

    def test_contains_scam_score(self):
        self.assertIn("2/10", self.text)

    def test_contains_pros(self):
        self.assertIn("Close to airport", self.text)

    def test_contains_cons(self):
        self.assertIn("Small kitchen", self.text)

    def test_contains_summary(self):
        self.assertIn("Solid option for the internship period.", self.text)

    def test_contains_url(self):
        self.assertIn("https://www.wg-gesucht.de/abc123", self.text)

    def test_location_strips_city_prefix(self):
        # Location "Hamburg | Winterhude | Musterstraße" → shows parts after first pipe
        self.assertIn("Winterhude", self.text)

    def test_scam_reason_shown_when_present(self):
        analysis = dict(self.analysis, scam_reason="Suspicious price drop.")
        text = telegram_mod.format_listing_with_ai(self.listing, analysis)
        self.assertIn("Suspicious price drop.", text)

    def test_scam_reason_absent_when_empty(self):
        # No extra italic line when scam_reason is empty
        self.assertNotIn("</i>\n", self.text.split("Scam")[1].split("\n")[0])

    def test_missing_analysis_keys_handled(self):
        # Should not raise even with minimal analysis dict
        minimal = {"recommendation_score": 5, "scam_score": 3}
        text = telegram_mod.format_listing_with_ai(self.listing, minimal)
        self.assertIn("5/10", text)

    def test_pros_capped_at_three(self):
        analysis = dict(self.analysis, pros=["P1", "P2", "P3", "P4", "P5"])
        text = telegram_mod.format_listing_with_ai(self.listing, analysis)
        self.assertIn("P3", text)
        self.assertNotIn("P4", text)

    def test_cons_capped_at_three(self):
        analysis = dict(self.analysis, cons=["C1", "C2", "C3", "C4"])
        text = telegram_mod.format_listing_with_ai(self.listing, analysis)
        self.assertIn("C3", text)
        self.assertNotIn("C4", text)

    def test_empty_pros_shows_dash(self):
        analysis = dict(self.analysis, pros=[])
        text = telegram_mod.format_listing_with_ai(self.listing, analysis)
        self.assertIn("✅ —", text)

    def test_empty_cons_shows_dash(self):
        analysis = dict(self.analysis, cons=[])
        text = telegram_mod.format_listing_with_ai(self.listing, analysis)
        self.assertIn("⚠️ —", text)


class TestSend(unittest.TestCase):
    def test_returns_false_when_not_configured(self):
        with patch.object(telegram_mod, "BOT_TOKEN", ""), \
             patch.object(telegram_mod, "CHAT_ID", ""):
            result = telegram_mod.send("hello")
        self.assertFalse(result)

    def test_calls_send_once_on_success(self):
        with patch.object(telegram_mod, "BOT_TOKEN", "token123"), \
             patch.object(telegram_mod, "CHAT_ID", "chat456"), \
             patch.object(telegram_mod, "_send_once", return_value=True) as mock_send:
            result = telegram_mod.send("hello")
        self.assertTrue(result)
        mock_send.assert_called_once_with("hello")

    def test_retries_once_on_first_failure(self):
        with patch.object(telegram_mod, "BOT_TOKEN", "token123"), \
             patch.object(telegram_mod, "CHAT_ID", "chat456"), \
             patch.object(telegram_mod, "_send_once", side_effect=[False, True]) as mock_send, \
             patch("time.sleep"):
            result = telegram_mod.send("hello")
        self.assertTrue(result)
        self.assertEqual(mock_send.call_count, 2)

    def test_returns_false_after_two_failures(self):
        with patch.object(telegram_mod, "BOT_TOKEN", "token123"), \
             patch.object(telegram_mod, "CHAT_ID", "chat456"), \
             patch.object(telegram_mod, "_send_once", return_value=False), \
             patch("time.sleep"):
            result = telegram_mod.send("hello")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
