"""Golden-value unit tests for lunarcal.

These tests are the "golden values" that the engine must reproduce exactly.
They cover CNY dates, leap months, solar-term dates, ganzhi, festivals,
shujiu and sanfu.
"""

import unittest

from lunarcal import (
    LunarRangeError,
    all_solar_terms,
    day_ganzhi_str,
    festivals_on,
    leap_month_of_year,
    lunar_to_solar,
    sanfu_period,
    shujiu_period,
    solar_term_on,
    solar_to_lunar,
    year_ganzhi_str,
    zodiac_year,
)


class TestCNYGolden(unittest.TestCase):
    """春节 (正月初一) Gregorian dates -- must match exactly."""

    CASES = [
        (2020, (2020, 1, 25)),
        (2021, (2021, 2, 12)),
        (2022, (2022, 2, 1)),
        (2023, (2023, 1, 22)),
        (2024, (2024, 2, 10)),
        (2025, (2025, 1, 29)),
        (2026, (2026, 2, 17)),
    ]

    def test_cny_dates(self):
        for lunar_year, expected in self.CASES:
            with self.subTest(lunar_year=lunar_year):
                got = lunar_to_solar(lunar_year, 1, 1, is_leap=False)
                self.assertEqual(got, expected,
                                 f"CNY {lunar_year} mismatch: got {got}, want {expected}")

    def test_roundtrip(self):
        for y, m, d in [(2024, 2, 10), (2025, 1, 29), (2026, 2, 17)]:
            ld = solar_to_lunar(y, m, d)
            self.assertEqual(ld.lunar_month, 1)
            self.assertEqual(ld.lunar_day, 1)
            self.assertFalse(ld.is_leap)


class TestLeapMonths(unittest.TestCase):
    def test_leap_months(self):
        cases = [(2017, 6), (2020, 4), (2023, 2), (2025, 6)]
        for ly, want in cases:
            with self.subTest(lunar_year=ly):
                self.assertEqual(leap_month_of_year(ly), want)

    def test_non_leap_year(self):
        self.assertEqual(leap_month_of_year(2024), 0)
        self.assertEqual(leap_month_of_year(2026), 0)


class TestSolarTerms(unittest.TestCase):
    def test_chunfen_2024(self):
        st = solar_term_on(2024, "春分")
        self.assertEqual((st.year, st.month, st.day), (2024, 3, 20))
        # time should be ~11:00 Beijing (within 15 minutes)
        self.assertAlmostEqual(st.hour * 60 + st.minute, 11 * 60 + 6, delta=15)

    def test_dongzhi_2024(self):
        st = solar_term_on(2024, "冬至")
        self.assertEqual((st.year, st.month, st.day), (2024, 12, 21))
        # ~17:20 Beijing
        self.assertAlmostEqual(st.hour * 60 + st.minute, 17 * 60 + 20, delta=15)

    def test_xiazhi_2024(self):
        st = solar_term_on(2024, "夏至")
        self.assertEqual((st.year, st.month, st.day), (2024, 6, 21))

    def test_24_terms_present(self):
        terms = all_solar_terms(2024)
        names = {t.name_zh for t in terms}
        self.assertIn("春分", names)
        self.assertIn("冬至", names)
        self.assertIn("立春", names)
        self.assertIn("清明", names)


class TestGanzhi(unittest.TestCase):
    def test_year_ganzhi(self):
        self.assertEqual(year_ganzhi_str(2024), "甲辰")
        self.assertEqual(year_ganzhi_str(2025), "乙巳")
        self.assertEqual(zodiac_year(2024), "龙")
        self.assertEqual(zodiac_year(2025), "蛇")

    def test_day_ganzhi_known(self):
        # 2000-01-01 was 戊午 day (anchor)
        self.assertEqual(day_ganzhi_str(2000, 1, 1), "戊午")
        # 2024-02-10 (CNY) day ganzhi -- cross-check
        self.assertEqual(day_ganzhi_str(2024, 2, 10), "甲辰")


class TestFestivals(unittest.TestCase):
    def test_cny_is_spring_festival(self):
        evs = festivals_on(2024, 2, 10)
        names = [e.name_zh for e in evs]
        self.assertIn("春节", names)

    def test_mid_autumn_2024(self):
        # Mid-Autumn 2024 = Sep 17
        gy, gm, gd = lunar_to_solar(2024, 8, 15)
        self.assertEqual((gy, gm, gd), (2024, 9, 17))

    def test_duanwu_2024(self):
        gy, gm, gd = lunar_to_solar(2024, 5, 5)
        self.assertEqual((gy, gm, gd), (2024, 6, 10))


class TestShujiuSanfu(unittest.TestCase):
    def test_shujiu_starts_dongzhi(self):
        # Dongzhi 2024 = Dec 21. Dec 21 should be 一九第1天.
        sj = shujiu_period(2024, 12, 21)
        self.assertIsNotNone(sj)
        self.assertEqual(sj[0], "一九")
        self.assertEqual(sj[1], 1)

    def test_sanfu_2024(self):
        sf = sanfu_period(2024)
        self.assertEqual(sf["初伏"], (2024, 7, 15))
        self.assertEqual(sf["末伏"], (2024, 8, 14))


class TestRangeError(unittest.TestCase):
    def test_out_of_range(self):
        with self.assertRaises(LunarRangeError):
            solar_to_lunar(1899, 6, 1)
        with self.assertRaises(LunarRangeError):
            solar_to_lunar(2101, 6, 1)


if __name__ == "__main__":
    unittest.main()
