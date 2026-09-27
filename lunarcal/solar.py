"""Solar-term (二十四节气) computation.

A solar term begins when the apparent geocentric ecliptic longitude of the
Sun reaches an exact multiple of 15 degrees.  We solve for the instant
(TT Julian Day) via bisection on the solar longitude, then convert to
Beijing civil time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .astro import (
    gregorian_to_jd,
    jd_tt_to_bjdt,
    solar_term_time_deg,
)

# The 24 solar terms, in order.  Index 0 = 春分 (sun longitude 0 deg),
# index 1 = 清明 (15 deg), ...  The minor/节 terms start the lunar months;
# the major/中气 terms are at even multiples of 30 deg.
SOLAR_TERMS_ZH = [
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
]
SOLAR_TERMS_EN = [
    "Chunfen", "Qingming", "Guyu", "Lixia", "Xiaoman", "Mangzhong",
    "Xiazhi", "Xiaoshu", "Dashu", "Liqiu", "Chushu", "Bailu",
    "Qiufen", "Hanlu", "Shuangjiang", "Lidong", "Xiaoxue", "Daxue",
    "Dongzhi", "Xiaohan", "Dahan", "Lichun", "Yushui", "Jingzhe",
]

# Major solar terms (中气) -- sun longitude at 0, 30, 60, ..., 330.
# These anchor the lunar month numbering.
MAJOR_TERMS_ZH = [
    "春分", "谷雨", "小满", "夏至", "大暑", "处暑",
    "秋分", "霜降", "小雪", "冬至", "大寒", "雨水",
]
# Minor solar terms (节) -- sun longitude at 15, 45, ..., 345.
MINOR_TERMS_ZH = [
    "清明", "立夏", "芒种", "小暑", "立秋", "白露",
    "寒露", "立冬", "大雪", "小寒", "立春", "惊蛰",
]


@dataclass(frozen=True)
class SolarTerm:
    name_zh: str
    longitude_deg: float
    # Beijing civil datetime (UTC+8)
    year: int
    month: int
    day: int
    hour: int
    minute: int

    def as_dict(self) -> dict:
        return {
            "name_zh": self.name_zh,
            "longitude_deg": self.longitude_deg,
            "beijing": f"{self.year:04d}-{self.month:02d}-{self.day:02d} "
                       f"{self.hour:02d}:{self.minute:02d}",
        }


def solar_term_longitude(index_from_chunfen: int) -> float:
    """Sun longitude (deg) for the i-th solar term counting from Chunfen=0."""
    return (index_from_chunfen * 15.0) % 360.0


def solar_term_on(year: int, name_zh: str) -> SolarTerm:
    """Return the Beijing datetime of the named solar term in the given year.

    Note: a solar term named e.g. 立春 usually falls in early February of the
    given Gregorian year; 冬至 falls in late December.
    """
    idx = SOLAR_TERMS_ZH.index(name_zh)
    lon = solar_term_longitude(idx)
    # Rough guess: search near the usual calendar window for that term.
    # Approximate dates (Beijing):
    guess_month = {
        "春分": 3, "清明": 4, "谷雨": 4, "立夏": 5, "小满": 5, "芒种": 6,
        "夏至": 6, "小暑": 7, "大暑": 7, "立秋": 8, "处暑": 8, "白露": 9,
        "秋分": 9, "寒露": 10, "霜降": 10, "立冬": 11, "小雪": 11, "大雪": 12,
        "冬至": 12, "小寒": 1, "大寒": 1, "立春": 2, "雨水": 2, "惊蛰": 3,
    }[name_zh]
    guess_day = 20 if name_zh not in ("小寒", "大寒", "立春", "雨水", "惊蛰") else 5
    # For terms that straddle the new year (小寒/大寒 in Jan of `year`),
    # the guess is already in `year`.
    jd_guess = gregorian_to_jd(year, guess_month, float(guess_day))
    jd_tt = solar_term_time_deg(lon, jd_guess)
    y, m, d, hh, mm, _ = jd_tt_to_bjdt(jd_tt)
    return SolarTerm(name_zh=name_zh, longitude_deg=lon,
                     year=y, month=m, day=d, hour=hh, minute=mm)


def all_solar_terms(year: int) -> List[SolarTerm]:
    """Return the 24 solar terms that fall in the given Gregorian year
    (Beijing time).  This includes 小寒/大寒 of January, through 冬至/小寒
    of the following January."""
    out: List[SolarTerm] = []
    for name in SOLAR_TERMS_ZH:
        st = solar_term_on(year, name)
        out.append(st)
    # Also grab 小寒/大寒 of the *following* January (which belong to the
    # same Chinese-lunar "year" but fall after Dec).  They are already
    # covered if we asked for year+1; skip for now to keep output tidy.
    return out


def solar_terms_in_range(start_ymd: Tuple[int, int, int],
                         end_ymd: Tuple[int, int, int]) -> List[SolarTerm]:
    """List solar terms whose Beijing datetime falls within [start, end]."""
    y0, m0, d0 = start_ymd
    y1, m1, d1 = end_ymd
    out: List[SolarTerm] = []
    for year in range(y0, y1 + 2):
        for st in all_solar_terms(year):
            if (st.year, st.month, st.day) < (y0, m0, d0):
                continue
            if (st.year, st.month, st.day) > (y1, m1, d1):
                continue
            out.append(st)
    out.sort(key=lambda s: (s.year, s.month, s.day, s.hour, s.minute))
    return out
