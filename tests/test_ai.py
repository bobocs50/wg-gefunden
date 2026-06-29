import unittest
from unittest.mock import patch, MagicMock

import src.ai as ai_mod
from src.listing import Listing


def make_listing(**kwargs) -> Listing:
    defaults = dict(
        id="abc123",
        title="Schöne Wohnung",
        price_text="800 €",
        location="Hamburg | Winterhude",
        date_text="01.08.2026 - 31.01.2027",
        date_start="01.08.2026",
        date_end="31.01.2027",
        last_online="28.06.2026",
        url="https://www.wg-gesucht.de/abc123",
        wg_type_code="",
    )
    defaults.update(kwargs)
    return Listing(**defaults)


class TestBulletList(unittest.TestCase):
    def test_formats_items(self):
        result = ai_mod._bullet_list(["Item A", "Item B"])
        self.assertIn("- Item A", result)
        self.assertIn("- Item B", result)

    def test_empty_list_returns_placeholder(self):
        result = ai_mod._bullet_list([])
        self.assertEqual(result, "- Not specified")

    def test_single_item(self):
        result = ai_mod._bullet_list(["Only one"])
        self.assertEqual(result, "- Only one")

    def test_multiple_items_joined_by_newline(self):
        result = ai_mod._bullet_list(["A", "B", "C"])
        lines = result.split("\n")
        self.assertEqual(len(lines), 3)


class TestListingBlock(unittest.TestCase):
    def test_contains_title(self):
        listing = make_listing()
        block = ai_mod._listing_block(listing)
        self.assertIn("Schöne Wohnung", block)

    def test_contains_price(self):
        listing = make_listing()
        block = ai_mod._listing_block(listing)
        self.assertIn("800 €", block)

    def test_contains_location(self):
        listing = make_listing()
        block = ai_mod._listing_block(listing)
        self.assertIn("Hamburg | Winterhude", block)

    def test_contains_dates(self):
        listing = make_listing()
        block = ai_mod._listing_block(listing)
        self.assertIn("01.08.2026", block)
        self.assertIn("31.01.2027", block)


class TestValidate(unittest.TestCase):
    def _valid_data(self, **kwargs):
        data = {
            "scam_score": 3,
            "recommendation_score": 7,
            "pros": ["Good location"],
            "cons": ["Small"],
            "summary": "Decent place.",
            "scam_reason": "",
        }
        data.update(kwargs)
        return data

    def test_valid_data_passes(self):
        result = ai_mod._validate(self._valid_data())
        self.assertEqual(result["scam_score"], 3)
        self.assertEqual(result["recommendation_score"], 7)

    def test_missing_required_key_raises(self):
        data = {"recommendation_score": 7}
        with self.assertRaises(ValueError):
            ai_mod._validate(data)

    def test_missing_both_required_keys_raises(self):
        with self.assertRaises(ValueError):
            ai_mod._validate({})

    def test_scores_clamped_to_1_10(self):
        result = ai_mod._validate(self._valid_data(scam_score=99, recommendation_score=0))
        self.assertEqual(result["scam_score"], 10)
        self.assertEqual(result["recommendation_score"], 1)

    def test_scores_clamped_at_lower_bound(self):
        result = ai_mod._validate(self._valid_data(scam_score=-5))
        self.assertEqual(result["scam_score"], 1)

    def test_non_list_pros_replaced_with_empty_list(self):
        result = ai_mod._validate(self._valid_data(pros="not a list"))
        self.assertEqual(result["pros"], [])

    def test_non_list_cons_replaced_with_empty_list(self):
        result = ai_mod._validate(self._valid_data(cons=42))
        self.assertEqual(result["cons"], [])

    def test_missing_summary_defaults_to_empty_string(self):
        data = {"scam_score": 3, "recommendation_score": 7}
        result = ai_mod._validate(data)
        self.assertEqual(result["summary"], "")

    def test_missing_scam_reason_defaults_to_empty_string(self):
        data = {"scam_score": 3, "recommendation_score": 7}
        result = ai_mod._validate(data)
        self.assertEqual(result["scam_reason"], "")

    def test_non_string_summary_replaced(self):
        result = ai_mod._validate(self._valid_data(summary=123))
        self.assertEqual(result["summary"], "")

    def test_scores_converted_from_string(self):
        result = ai_mod._validate(self._valid_data(scam_score="4", recommendation_score="8"))
        self.assertEqual(result["scam_score"], 4)
        self.assertEqual(result["recommendation_score"], 8)


class TestAnalyze(unittest.TestCase):
    def test_returns_none_without_api_key(self):
        listing = make_listing()
        with patch.dict("os.environ", {}, clear=True):
            # Ensure OPENAI_API_KEY is absent
            import os
            os.environ.pop("OPENAI_API_KEY", None)
            result = ai_mod.analyze(listing, "some detail text")
        self.assertIsNone(result)

    def test_returns_validated_dict_on_success(self):
        listing = make_listing()
        fake_response_data = {
            "scam_score": 2,
            "recommendation_score": 8,
            "pros": ["Great location"],
            "cons": ["Bit expensive"],
            "summary": "Good match.",
            "scam_reason": "",
        }

        mock_message = MagicMock()
        mock_message.content = __import__("json").dumps(fake_response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}), \
             patch.object(ai_mod, "_client", mock_client):
            result = ai_mod.analyze(listing, "detail text")

        self.assertIsNotNone(result)
        self.assertEqual(result["recommendation_score"], 8)
        self.assertEqual(result["scam_score"], 2)

    def test_returns_none_on_api_exception(self):
        listing = make_listing()
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("network error")

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}), \
             patch.object(ai_mod, "_client", mock_client):
            result = ai_mod.analyze(listing, "detail text")

        self.assertIsNone(result)

    def test_returns_none_on_invalid_json(self):
        listing = make_listing()
        mock_message = MagicMock()
        mock_message.content = "not valid json {"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}), \
             patch.object(ai_mod, "_client", mock_client):
            result = ai_mod.analyze(listing, "detail text")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
