"""Lunar (Chinese) calendar conversion.

Algorithm (self-contained, based on the public "synodic month +
no-major-qi-means-leap-month" rule):

1. Every lunar month begins on the day (Beijing civil time) of a new moon.
2. The lunar month that contains the winter solstice (冬至, sun longitude
   270 deg) is the 11th month (冬月) of that lunar year.
3. Subsequent months are numbered 12, 1, 2, ... up to the next 11th month.
4. If any lunar month *after* the 11th month contains no 中气 (major solar
   term at an even multiple of 30 deg sun longitude), it is a leap month
   and inherits the number of the preceding (non-leap) month.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import List, Tuple

from .astro import (
    gregorian_to_jd,
    jd_tt_to_bjdt,
    new_moon_jd,
    solar_term_time_deg,
)

YEAR_MIN = 1900
YEAR_MAX = 2100


class LunarRangeError(ValueError):
    """Raised when a date is outside the supported 1900-2100 window."""


def _check_year(y: int) -> None:
    if not (YEAR_MIN <= y <= YEAR_MAX):
        raise LunarRangeError(
            f"lunarcal supports years {YEAR_MIN}-{YEAR_MAX} (requested {y})."
        )


# ---------------------------------------------------------------------------
# New moons (Beijing date)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _new_moons() -> List[Tuple[int, int, int, int, int]]:
    """Return list of (year, month, day, hour, minute) for every new moon
    between ~1899 and ~2101, Beijing civil time."""
    # k=0 is 2000-01-06.  Step back/forward to cover 1899-2102.
    # ~12.368 synodic months per year.
    out: List[Tuple[int, int, int, int, int]] = []
    k = -1250  # ~1900-01
    while True:
        jd = new_moon_jd(k)
        y, m, d, hh, mm, _ = jd_tt_to_bjdt(jd)
        if y > 2102:
            break
        if y >= 1899:
            out.append((y, m, d, hh, mm))
        k += 1
    return out


@lru_cache(maxsize=1)
def _major_zhongqi() -> List[Tuple[int, int, int, int, int, float]]:
    """List of (y, m, d, hh, mm, longitude) for all 中气 (major solar terms,
    sun longitude at even multiples of 30 deg) between 1899 and 2102."""
    longs = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
    names = ["春分", "谷雨", "小满", "夏至", "大暑", "处暑",
             "秋分", "霜降", "小雪", "冬至", "大寒", "雨水"]
    out = []
    for y in range(1899, 2103):
        for lon, nm in zip(longs, names):
            # rough guess
            guess_month = {
                "春分": 3, "谷雨": 4, "小满": 5, "夏至": 6, "大暑": 7,
                "处暑": 8, "秋分": 9, "霜降": 10, "小雪": 11, "冬至": 12,
                "大寒": 1, "雨水": 2,
            }[nm]
            guess_day = 21 if nm not in ("大寒", "雨水") else 20
            jd_guess = gregorian_to_jd(y, guess_month, float(guess_day))
            jd = solar_term_time_deg(lon, jd_guess)
            yy, mm, dd, hh, mi, _ = jd_tt_to_bjdt(jd)
            out.append((yy, mm, dd, hh, mi, float(lon)))
    out.sort()
    return out


@dataclass(frozen=True)
class LunarMonth:
    """A lunar month interval, anchored by its first day (Beijing)."""
    index: int                # index into _new_moons()
    year: int                 # Gregorian year of the new moon
    month: int
    day: int
    # month number 1..12, 0 means "unassigned"
    lunar_month: int = 0
    is_leap: bool = False
    lunar_year: int = 0       # the lunar year this month belongs to


@lru_cache(maxsize=1)
def _build_months() -> List[LunarMonth]:
    moons = _new_moons()
    zq = _major_zhongqi()
    months: List[LunarMonth] = []
    for i, (y, m, d, hh, mm) in enumerate(moons):
        months.append(LunarMonth(index=i, year=y, month=m, day=d))

    # For each month, collect the 中气 that fall in (start, next_start].
    # A 中气 on the start day itself belongs to the *previous* month's last
    # day convention; in practice we assign by comparing (ymd) ordering.
    def ymd(t):
        return (t[0], t[1], t[2])

    starts = [ymd((m.year, m.month, m.day)) for m in months]

    def month_has_zhongqi(i: int) -> bool:
        s0 = starts[i]
        s1 = starts[i + 1] if i + 1 < len(starts) else (9999, 12, 31)
        for z in zq:
            zymd = (z[0], z[1], z[2])
            if s0 <= zymd < s1:
                return True
        return False

    # Find 冬至 for each solar year, then locate the lunar month containing
    # it.  That month is the 11th month of the lunar year.
    # Lunar year Y roughly starts at the new moon on/after 立春 and ends
    # just before the next 11th month.  We anchor by 冬至.
    #
    # Strategy: for each 冬至 (lon=270), find the lunar month i such that
    # starts[i] <= dongzhi_date < starts[i+1].  Mark months[i].lunar_month=11.
    # Then walk forward: assign 12, 1, 2, ...; when a month has no 中气,
    # mark it leap (same number as previous).
    dongzhis = [z for z in zq if abs(z[5] - 270.0) < 0.01]

    # For each 冬至, find its containing lunar month.
    anchors = []  # (month_index, lunar_year)
    for dz in dongzhis:
        dzymd = (dz[0], dz[1], dz[2])
        # find i such that starts[i] <= dzymd < starts[i+1]
        for i in range(len(starts) - 1):
            if starts[i] <= dzymd < starts[i + 1]:
                # The lunar year that contains this 冬至 is the lunar year
                # that starts at the previous 正月.  By convention, lunar
                # year Y is the one whose 11th month contains the 冬至 in
                # Gregorian year Y (i.e. the lunar year starting in early Y).
                anchors.append((i, dz[0]))
                break

    # Now walk from each anchor: mark the anchor month as 11, then walk
    # forward until the next anchor (the next 11th month).
    for ai, (anchor_idx, lunaryear) in enumerate(anchors):
        next_anchor = anchors[ai + 1][0] if ai + 1 < len(anchors) else len(months) - 1
        # Assign numbers from anchor_idx forward.
        months[anchor_idx] = LunarMonth(
            index=months[anchor_idx].index, year=months[anchor_idx].year,
            month=months[anchor_idx].month, day=months[anchor_idx].day,
            lunar_month=11, is_leap=False, lunar_year=lunaryear,
        )
        cur_num = 11
        for j in range(anchor_idx + 1, next_anchor + 1):
            if j == next_anchor:
                # This is the next 11th month.
                months[j] = LunarMonth(
                    index=months[j].index, year=months[j].year,
                    month=months[j].month, day=months[j].day,
                    lunar_month=11, is_leap=False,
                    lunar_year=lunaryear + 1,
                )
                break
            if month_has_zhongqi(j):
                cur_num = cur_num + 1
                if cur_num > 12:
                    cur_num = 1
                months[j] = LunarMonth(
                    index=months[j].index, year=months[j].year,
                    month=months[j].month, day=months[j].day,
                    lunar_month=cur_num, is_leap=False,
                    lunar_year=lunaryear if cur_num >= 11 else lunaryear + 1,
                )
            else:
                # Leap month: keep cur_num, mark leap.
                months[j] = LunarMonth(
                    index=months[j].index, year=months[j].year,
                    month=months[j].month, day=months[j].day,
                    lunar_month=cur_num, is_leap=True,
                    lunar_year=lunaryear if cur_num >= 11 else lunaryear + 1,
                )
    return months


# Chinese lunar month names (1..12)
_LUNAR_MONTH_NAMES = [
    "正月", "二月", "三月", "四月", "五月", "六月",
    "七月", "八月", "九月", "十月", "冬月", "腊月",
]
_LUNAR_DAY_NAMES_1_10 = ["初一", "初二", "初三", "初四", "初五",
                         "初六", "初七", "初八", "初九", "初十"]
_LUNAR_DAY_NAMES_11_20 = ["十一", "十二", "十三", "十四", "十五",
                          "十六", "十七", "十八", "十九", "二十"]
_LUNAR_DAY_NAMES_21_30 = ["廿一", "廿二", "廿三", "廿四", "廿五",
                          "廿六", "廿七", "廿八", "廿九", "三十"]


def _day_name(day: int) -> str:
    if day <= 10:
        return _LUNAR_DAY_NAMES_1_10[day - 1]
    if day <= 20:
        return _LUNAR_DAY_NAMES_11_20[day - 11]
    return _LUNAR_DAY_NAMES_21_30[day - 21]


@dataclass(frozen=True)
class LunarDate:
    lunar_year: int
    lunar_month: int        # 1..12
    lunar_day: int          # 1..30
    is_leap: bool
    # Gregorian date that this lunar date falls on
    gregorian_year: int
    gregorian_month: int
    gregorian_day: int

    def month_name(self) -> str:
        prefix = "闰" if self.is_leap else ""
        return prefix + _LUNAR_MONTH_NAMES[self.lunar_month - 1]

    def day_name(self) -> str:
        return _day_name(self.lunar_day)

    def chinese_str(self) -> str:
        return f"{self.lunar_year}年{self.month_name()}{self.day_name()}"

    def as_dict(self) -> dict:
        return {
            "lunar_year": self.lunar_year,
            "lunar_month": self.lunar_month,
            "lunar_day": self.lunar_day,
            "is_leap": self.is_leap,
            "month_name_zh": self.month_name(),
            "day_name_zh": self.day_name(),
            "gregorian": f"{self.gregorian_year:04d}-{self.gregorian_month:02d}-{self.gregorian_day:02d}",
        }


def solar_to_lunar(year: int, month: int, day: int) -> LunarDate:
    """Convert a Gregorian date to a lunar date (Beijing calendar)."""
    _check_year(year)
    months = _build_months()
    target = (year, month, day)
    # Find the lunar month i such that starts[i] <= target < starts[i+1]
    starts = [(m.year, m.month, m.day) for m in months]
    found = None
    for i in range(len(starts) - 1):
        if starts[i] <= target < starts[i + 1]:
            found = i
            break
    if found is None:
        raise LunarRangeError(f"Date {year}-{month}-{day} out of range.")
    lm = months[found]
    if lm.lunar_month == 0:
        # unassigned (edge boundary); pick nearest
        raise LunarRangeError(f"Date {year}-{month}-{day} out of supported range.")
    day_num = (
        (gregorian_to_jd(year, month, day) -
         gregorian_to_jd(lm.year, lm.month, lm.day))
    )
    day_num = int(round(day_num)) + 1
    # clamp to 29/30
    return LunarDate(
        lunar_year=lm.lunar_year,
        lunar_month=lm.lunar_month,
        lunar_day=day_num,
        is_leap=lm.is_leap,
        gregorian_year=year,
        gregorian_month=month,
        gregorian_day=day,
    )


def lunar_to_solar(lunar_year: int, lunar_month: int, lunar_day: int,
                   is_leap: bool = False) -> Tuple[int, int, int]:
    """Convert a lunar date back to Gregorian (y, m, d)."""
    _check_year(lunar_year)
    months = _build_months()
    for m in months:
        if (m.lunar_year == lunar_year and m.lunar_month == lunar_month
                and m.is_leap == is_leap and m.lunar_month != 0):
            # compute day offset
            jd0 = gregorian_to_jd(m.year, m.month, m.day)
            jd_target = jd0 + (lunar_day - 1)
            from .astro import jd_to_gregorian
            y, mo, d = jd_to_gregorian(jd_target + 8.0 / 24.0)
            # jd_to_gregorian returns float day; take floor
            return (y, mo, int(d))
    raise LunarRangeError(
        f"No such lunar date: {lunar_year}-{'闰' if is_leap else ''}{lunar_month}-{lunar_day}."
    )


def leap_month_of_year(lunar_year: int) -> int:
    """Return the leap month number (1..12) of the given lunar year, or 0
    if there is no leap month that year."""
    _check_year(lunar_year)
    months = _build_months()
    for m in months:
        if m.lunar_year == lunar_year and m.is_leap:
            return m.lunar_month
    return 0
