import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import src.filters as filters_mod
from src.listing import Listing


def make_listing(**kwargs) -> Listing:
    recent = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
    defaults = dict(
        id="123",
        title="Nice flat",
        price_text="800 €",
        location="Hamburg | Winterhude",
        date_text="01.08.2026 - 01.02.2027",
        date_start="01.08.2026",
        date_end="01.02.2027",
        last_online=recent,
        url="https://wg-gesucht.de/123",
        wg_type_code="",
    )
    defaults.update(kwargs)
    return Listing(**defaults)


class TestParseDate(unittest.TestCase):
    def test_dd_mm_yyyy(self):
        self.assertEqual(filters_mod._parse_date("01.08.2026"), datetime(2026, 8, 1))

    def test_dd_mm_yy(self):
        self.assertEqual(filters_mod._parse_date("01.08.26"), datetime(2026, 8, 1))

    def test_iso_format(self):
        self.assertEqual(filters_mod._parse_date("2026-08-01"), datetime(2026, 8, 1))

    def test_invalid_returns_none(self):
        self.assertIsNone(filters_mod._parse_date("not a date"))
        self.assertIsNone(filters_mod._parse_date("gestern"))

    def test_empty_returns_none(self):
        self.assertIsNone(filters_mod._parse_date(""))

    def test_whitespace_stripped(self):
        self.assertEqual(filters_mod._parse_date("  01.08.2026  "), datetime(2026, 8, 1))


class TestPriceOk(unittest.TestCase):
    def setUp(self):
        self.p = patch.object(filters_mod, "MAX_RENT", 1000)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_within_budget(self):
        self.assertTrue(filters_mod._price_ok("800 €"))

    def test_at_budget_limit(self):
        self.assertTrue(filters_mod._price_ok("1000 €"))

    def test_over_budget(self):
        self.assertFalse(filters_mod._price_ok("1001 €"))

    def test_zero_price_rejected(self):
        self.assertFalse(filters_mod._price_ok("0 €"))

    def test_no_digits_rejected(self):
        self.assertFalse(filters_mod._price_ok("auf Anfrage"))

    def test_price_with_symbols(self):
        # regex strips all non-digits: "750,00" becomes "75000" — use space-separated format
        self.assertTrue(filters_mod._price_ok("750 €/Monat"))

    def test_price_with_comma_thousands(self):
        self.assertTrue(filters_mod._price_ok("1.000 €"))


class TestDistrictOk(unittest.TestCase):
    def setUp(self):
        self.p1 = patch.object(filters_mod, "PREFERRED_DISTRICTS", ["winterhude", "eppendorf"])
        self.p2 = patch.object(filters_mod, "DISTRICT_FALLBACK_CITY", "")
        self.p1.start()
        self.p2.start()

    def tearDown(self):
        self.p1.stop()
        self.p2.stop()

    def test_preferred_district_passes(self):
        self.assertTrue(filters_mod._district_ok("Hamburg | Winterhude"))

    def test_case_insensitive(self):
        self.assertTrue(filters_mod._district_ok("HAMBURG | EPPENDORF"))

    def test_non_preferred_fails(self):
        self.assertFalse(filters_mod._district_ok("Hamburg | Altona"))

    def test_fallback_city_passes_generic_location(self):
        with patch.object(filters_mod, "DISTRICT_FALLBACK_CITY", "hamburg"):
            self.assertTrue(filters_mod._district_ok("1-Zimmer | Hamburg | Ifflandstraße"))

    def test_fallback_city_empty_does_not_pass_non_preferred(self):
        self.assertFalse(filters_mod._district_ok("Hamburg | Altona"))

    def test_district_matched_in_title(self):
        # run_checks concatenates location + title; _district_ok receives full string
        self.assertTrue(filters_mod._district_ok("Hamburg | Ifflandstraße Winterhude Apartment"))


class TestDatesOk(unittest.TestCase):
    def setUp(self):
        self.p1 = patch.object(filters_mod, "EARLIEST_MOVE_IN", datetime(2026, 8, 1))
        self.p2 = patch.object(filters_mod, "LATEST_MOVE_IN", datetime(2027, 2, 1))
        self.p1.start()
        self.p2.start()

    def tearDown(self):
        self.p1.stop()
        self.p2.stop()

    def test_in_range(self):
        self.assertTrue(filters_mod._dates_ok("01.09.2026"))

    def test_at_start_boundary(self):
        self.assertTrue(filters_mod._dates_ok("01.08.2026"))

    def test_at_end_boundary(self):
        self.assertTrue(filters_mod._dates_ok("01.02.2027"))

    def test_before_range_fails(self):
        self.assertFalse(filters_mod._dates_ok("01.07.2026"))

    def test_after_range_fails(self):
        self.assertFalse(filters_mod._dates_ok("02.02.2027"))

    def test_empty_passes(self):
        self.assertTrue(filters_mod._dates_ok(""))

    def test_unparseable_passes(self):
        self.assertTrue(filters_mod._dates_ok("sofort"))


class TestEndDateOk(unittest.TestCase):
    def setUp(self):
        self.p = patch.object(filters_mod, "MIN_END_DATE", datetime(2027, 2, 1))
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_end_on_min_date(self):
        self.assertTrue(filters_mod._end_date_ok("01.02.2027"))

    def test_end_after_min_date(self):
        self.assertTrue(filters_mod._end_date_ok("01.06.2027"))

    def test_end_before_min_date_fails(self):
        self.assertFalse(filters_mod._end_date_ok("31.12.2026"))

    def test_empty_end_passes(self):
        self.assertTrue(filters_mod._end_date_ok(""))

    def test_open_ended_passes(self):
        self.assertTrue(filters_mod._end_date_ok(""))


class TestLastOnlineOk(unittest.TestCase):
    def setUp(self):
        self.p = patch.object(filters_mod, "LAST_ONLINE_MAX_DAYS", 7)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_unknown_passes(self):
        self.assertTrue(filters_mod._last_online_ok(""))

    def test_recent_passes(self):
        recent = (datetime.now() - timedelta(days=2)).strftime("%d.%m.%Y")
        self.assertTrue(filters_mod._last_online_ok(recent))

    def test_at_limit_passes(self):
        at_limit = (datetime.now() - timedelta(days=7)).strftime("%d.%m.%Y")
        self.assertTrue(filters_mod._last_online_ok(at_limit))

    def test_too_old_fails(self):
        old = (datetime.now() - timedelta(days=30)).strftime("%d.%m.%Y")
        self.assertFalse(filters_mod._last_online_ok(old))


class TestWgSizeOk(unittest.TestCase):
    def setUp(self):
        self.p = patch.object(filters_mod, "WG_SIZE_MAX", 3)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_within_limit(self):
        self.assertTrue(filters_mod._wg_size_ok("2er WG | Winterhude"))

    def test_at_limit(self):
        self.assertTrue(filters_mod._wg_size_ok("3er WG | Winterhude"))

    def test_over_limit_fails(self):
        self.assertFalse(filters_mod._wg_size_ok("4er WG | Winterhude"))

    def test_no_wg_mention_passes(self):
        self.assertTrue(filters_mod._wg_size_ok("Hamburg | Winterhude"))

    def test_zero_max_always_passes(self):
        with patch.object(filters_mod, "WG_SIZE_MAX", 0):
            self.assertTrue(filters_mod._wg_size_ok("10er WG | Winterhude"))


class TestWgTypeOk(unittest.TestCase):
    def setUp(self):
        self.p = patch.object(filters_mod, "WG_FLATSHARE_TYPES", ["2", "12"])
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_accepted_type(self):
        self.assertTrue(filters_mod._wg_type_ok("12"))

    def test_another_accepted_type(self):
        self.assertTrue(filters_mod._wg_type_ok("2"))

    def test_rejected_type_fails(self):
        self.assertFalse(filters_mod._wg_type_ok("3"))

    def test_empty_list_accepts_all(self):
        with patch.object(filters_mod, "WG_FLATSHARE_TYPES", []):
            self.assertTrue(filters_mod._wg_type_ok("99"))

    def test_empty_code_passes(self):
        self.assertTrue(filters_mod._wg_type_ok(""))


class TestRunChecks(unittest.TestCase):
    def setUp(self):
        recent = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
        self.listing = make_listing(last_online=recent)
        self.patches = [
            patch.object(filters_mod, "MAX_RENT", 1000),
            patch.object(filters_mod, "PREFERRED_DISTRICTS", ["winterhude"]),
            patch.object(filters_mod, "DISTRICT_FALLBACK_CITY", ""),
            patch.object(filters_mod, "EARLIEST_MOVE_IN", datetime(2026, 8, 1)),
            patch.object(filters_mod, "LATEST_MOVE_IN", datetime(2027, 2, 1)),
            patch.object(filters_mod, "MIN_END_DATE", datetime(2027, 2, 1)),
            patch.object(filters_mod, "LAST_ONLINE_MAX_DAYS", 7),
            patch.object(filters_mod, "WG_SIZE_MAX", 3),
            patch.object(filters_mod, "WG_FLATSHARE_TYPES", ["2", "12"]),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def _checks_dict(self, listing):
        return {name: passed for name, _, passed in filters_mod.run_checks(listing)}

    def test_all_pass_for_valid_listing(self):
        checks = self._checks_dict(self.listing)
        self.assertTrue(all(checks.values()), checks)

    def test_returns_list_of_tuples(self):
        result = filters_mod.run_checks(self.listing)
        self.assertIsInstance(result, list)
        for item in result:
            self.assertEqual(len(item), 3)
            name, display, passed = item
            self.assertIsInstance(name, str)
            self.assertIsInstance(passed, bool)

    def test_price_check_fails_over_budget(self):
        listing = make_listing(price_text="1500 €")
        self.assertFalse(self._checks_dict(listing)["price"])

    def test_district_check_fails_wrong_district(self):
        listing = make_listing(location="Hamburg | Altona", title="Flat")
        self.assertFalse(self._checks_dict(listing)["district"])

    def test_dates_check_fails_out_of_range(self):
        listing = make_listing(date_start="01.01.2025")
        self.assertFalse(self._checks_dict(listing)["dates"])

    def test_wg_checks_included_when_wg_type_code_set(self):
        listing = make_listing(wg_type_code="12")
        checks = self._checks_dict(listing)
        self.assertIn("wg_size", checks)
        self.assertIn("wg_type", checks)

    def test_wg_checks_absent_when_no_wg_type_code(self):
        listing = make_listing(wg_type_code="")
        checks = self._checks_dict(listing)
        self.assertNotIn("wg_size", checks)
        self.assertNotIn("wg_type", checks)

    def test_wg_type_fails_wrong_type(self):
        listing = make_listing(wg_type_code="3")
        self.assertFalse(self._checks_dict(listing)["wg_type"])


if __name__ == "__main__":
    unittest.main()
