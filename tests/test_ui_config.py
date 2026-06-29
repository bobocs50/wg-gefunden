import unittest
from datetime import date

from src.ui_config import build_config, lines_to_list, validate_form


def make_values(**overrides) -> dict:
    values = {
        "url": " https://example.com/search ",
        "max_rent": 1000,
        "move_in_from": date(2026, 8, 1),
        "move_in_to": date(2026, 9, 1),
        "stay_until": date(2027, 2, 1),
        "search_apartments": True,
        "search_wg": False,
        "furnished_only": False,
        "pets_allowed": False,
        "categories": [1, 2, 3],
        "last_online_max_days": 7,
        "max_pages": 1,
        "headless": True,
        "preferred_raw": "winterhude\n\neppendorf\n",
        "fallback_city": " Hamburg ",
        "wg_size_max": 3,
        "flatshare_types": ["2", "12"],
        "ai_enabled": True,
        "model": " gpt-4.1-mini ",
        "max_calls_per_run": 3,
        "max_detail_chars": 2500,
        "max_output_tokens": 400,
        "profile_name": " Apartment seeker ",
        "profile_context": " Looking for a short-term furnished apartment. ",
        "must_haves_raw": "Furnished\nSublet",
        "strong_prefs_raw": "Good transport",
        "nice_raw": "Balcony",
    }
    values.update(overrides)
    return values


class TestLinesToList(unittest.TestCase):
    def test_trims_and_skips_empty(self):
        self.assertEqual(lines_to_list(" a \n\n b "), ["a", "b"])


class TestValidateForm(unittest.TestCase):
    def test_valid_form_has_no_errors(self):
        self.assertEqual(validate_form(make_values()), [])

    def test_rejects_invalid_values(self):
        values = make_values(
            max_rent=0,
            url="   ",
            move_in_from=date(2026, 10, 1),
            move_in_to=date(2026, 9, 1),
            stay_until=date(2026, 8, 1),
            max_pages=0,
        )
        errors = validate_form(values)
        self.assertIn("Max rent must be > 0.", errors)
        self.assertIn("Search URL cannot be empty.", errors)
        self.assertIn("Move-in from must be ≤ move-in to.", errors)
        self.assertIn("Move-in to must be ≤ stay until.", errors)
        self.assertIn("Max pages must be ≥ 1.", errors)


class TestBuildConfig(unittest.TestCase):
    def test_preserves_unedited_keys_and_updates_known_values(self):
        existing = {
            "search": {"legacy_search_flag": True},
            "districts": {"legacy_district_flag": "keep"},
            "wg": {"legacy_wg_flag": 99},
            "ai": {"legacy_ai_flag": "x"},
            "profile": {"legacy_profile_flag": "y"},
            "telegram": {"chat_id": "12345"},
            "custom_section": {"value": "keep-me"},
        }

        cfg = build_config(existing, make_values())

        self.assertEqual(cfg["custom_section"], {"value": "keep-me"})
        self.assertEqual(cfg["telegram"], {"chat_id": "12345"})
        self.assertTrue(cfg["search"]["legacy_search_flag"])
        self.assertEqual(cfg["districts"]["legacy_district_flag"], "keep")
        self.assertEqual(cfg["wg"]["legacy_wg_flag"], 99)
        self.assertEqual(cfg["ai"]["legacy_ai_flag"], "x")
        self.assertEqual(cfg["profile"]["legacy_profile_flag"], "y")

        self.assertEqual(cfg["search"]["url"], "https://example.com/search")
        self.assertEqual(cfg["search"]["move_in_from"], "2026-08-01")
        self.assertEqual(cfg["search"]["move_in_to"], "2026-09-01")
        self.assertEqual(cfg["search"]["stay_until"], "2027-02-01")
        self.assertEqual(cfg["districts"]["preferred"], ["winterhude", "eppendorf"])
        self.assertEqual(cfg["districts"]["fallback_city"], "Hamburg")
        self.assertEqual(cfg["ai"]["model"], "gpt-4.1-mini")
        self.assertEqual(cfg["profile"]["name"], "Apartment seeker")
        self.assertEqual(
            cfg["profile"]["context"],
            "\nLooking for a short-term furnished apartment.\n",
        )


if __name__ == "__main__":
    unittest.main()
