"""Heavenly Stems / Earthly Branches (干支) and Chinese zodiac.

Year ganzhi is anchored by the solar year (starting at 立春, ~Feb 4),
following the traditional "八字" convention.  Day ganzhi is computed by
counting days from a known reference Julian Day.
"""

from __future__ import annotations

from .astro import gregorian_to_jd

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
ZODIAC = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# Reference: 1984-02-02 (立春 1984) is the start of 甲子 year.
# Year stem/branch cycle: 1984 = 甲子.
_YEAR_ANCHOR = 1984  # 甲子 year


def year_ganzhi(year: int) -> tuple:
    """Return (stem_idx, branch_idx) for the lunar/solar year.

    Uses the convention that 1984 is 甲子.  Note: the ganzhi year changes
    at 立春, not at CNY; for most folk purposes CNY is used, but we expose
    the astronomical (立春-based) year here."""
    diff = year - _YEAR_ANCHOR
    stem = diff % 10
    branch = diff % 12
    return stem, branch


def year_ganzhi_str(year: int) -> str:
    s, b = year_ganzhi(year)
    return STEMS[s] + BRANCHES[b]


def zodiac_year(year: int) -> str:
    _, b = year_ganzhi(year)
    return ZODIAC[b]


# Day ganzhi: reference Julian Day.  2000-01-01 was 戊午 day (stem 4, branch 6).
# Verified against known calendars.
_DAY_ANCHOR_JD = gregorian_to_jd(2000, 1, 1.0)  # 0h UT
_DAY_ANCHOR_STEM = 4   # 戊
_DAY_ANCHOR_BRANCH = 6  # 午


def day_ganzhi(year: int, month: int, day: int) -> tuple:
    """Return (stem_idx, branch_idx) for the given Gregorian day (Beijing date).

    We anchor on UT midnight JD and add the day count.  Because Beijing is
    UTC+8, a Beijing date's ganzhi flips at midnight Beijing = 16:00 UT.
    We approximate by using the JD of 0h UT of that Beijing date, which is
    JD = gregorian_to_jd(y,m,d) - 8/24.
    """
    jd_beijing_midnight = gregorian_to_jd(year, month, float(day)) - 8.0 / 24.0
    n = round(jd_beijing_midnight - _DAY_ANCHOR_JD)
    stem = (_DAY_ANCHOR_STEM + n) % 10
    branch = (_DAY_ANCHOR_BRANCH + n) % 12
    return stem, branch


def day_ganzhi_str(year: int, month: int, day: int) -> str:
    s, b = day_ganzhi(year, month, day)
    return STEMS[s] + BRANCHES[b]
