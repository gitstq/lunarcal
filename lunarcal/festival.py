"""Festivals, 数九 (Shǔjiǔ), 三伏 (Sānfú)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .astro import gregorian_to_jd, jd_to_gregorian
from .ganzhi import day_ganzhi
from .lunar import lunar_to_solar, solar_to_lunar, LunarDate
from .solar import solar_term_on


# ---------------------------------------------------------------------------
# Traditional lunar festivals (lunar_month, lunar_day, name)
# ---------------------------------------------------------------------------
TRADITIONAL_FESTIVALS = [
    (1, 1, "春节", "Spring Festival"),
    (1, 15, "元宵节", "Lantern Festival"),
    (2, 2, "龙抬头", "Longtaitou"),
    (5, 5, "端午节", "Dragon Boat Festival"),
    (7, 7, "七夕", "Qixi Festival"),
    (7, 15, "中元节", "Ghost Festival"),
    (8, 15, "中秋节", "Mid-Autumn Festival"),
    (9, 9, "重阳节", "Double Ninth Festival"),
    (12, 8, "腊八节", "Laba Festival"),
    (12, 23, "小年(北)", "Xiaonian (North)"),
    (12, 24, "小年(南)", "Xiaonian (South)"),
]

# Gregorian festivals (month, day, name)
MODERN_FESTIVALS = [
    (1, 1, "元旦", "New Year's Day"),
    (2, 14, "情人节", "Valentine's Day"),
    (3, 8, "妇女节", "Women's Day"),
    (5, 1, "劳动节", "Labour Day"),
    (5, 4, "青年节", "Youth Day"),
    (6, 1, "儿童节", "Children's Day"),
    (7, 1, "建党节", "CPC Founding Day"),
    (8, 1, "建军节", "Army Day"),
    (9, 10, "教师节", "Teacher's Day"),
    (10, 1, "国庆节", "National Day"),
    (12, 25, "圣诞节", "Christmas"),
]


@dataclass(frozen=True)
class DayEvent:
    name_zh: str
    name_en: str
    kind: str   # "traditional" / "modern" / "shujiu" / "sanfu" / "solar_term"

    def as_dict(self) -> dict:
        return {"name_zh": self.name_zh, "name_en": self.name_en, "kind": self.kind}


# ---------------------------------------------------------------------------
# Shujiu (数九): 9 nine-day periods starting on Winter Solstice.
# ---------------------------------------------------------------------------

_SHUJIU_NAMES = ["一九", "二九", "三九", "四九", "五九",
                 "六九", "七九", "八九", "九九"]


def shujiu_period(year: int, month: int, day: int) -> Optional[Tuple[str, int]]:
    """If the date falls in 数九, return (period_name, day_in_period).

    数九 runs from 冬至 (in Gregorian year `year`) for 81 days.
    """
    dz = solar_term_on(year, "冬至")
    dz_jd = gregorian_to_jd(dz.year, dz.month, float(dz.day))
    cur_jd = gregorian_to_jd(year, month, float(day))
    n = round(cur_jd - dz_jd)
    if 0 <= n < 81:
        return _SHUJIU_NAMES[n // 9], (n % 9) + 1
    # Also handle Jan-Feb of next year (数九 started in Dec of previous year)
    if month <= 2:
        dz_prev = solar_term_on(year - 1, "冬至")
        dz_jd = gregorian_to_jd(dz_prev.year, dz_prev.month, float(dz_prev.day))
        n = round(cur_jd - dz_jd)
        if 0 <= n < 81:
            return _SHUJIU_NAMES[n // 9], (n % 9) + 1
    return None


# ---------------------------------------------------------------------------
# Sanfu (三伏): 庚日 = day ganzhi stem == 庚 (index 6).
# ---------------------------------------------------------------------------

def _is_geng_day(year: int, month: int, day: int) -> bool:
    stem, _ = day_ganzhi(year, month, day)
    return stem == 6  # 庚


def sanfu_period(year: int) -> dict:
    """Return {初伏: (y,m,d), 中伏: ..., 末伏: ...} for the given Gregorian year."""
    # 夏至: find 3rd 庚日 after it.
    xz = solar_term_on(year, "夏至")
    lq = solar_term_on(year, "立秋")

    def next_geng_on_or_after(start_jd: float, count: int) -> Tuple[int, int, int]:
        jd = start_jd
        found = 0
        while True:
            y, m, d = jd_to_gregorian(jd)
            d = int(d)
            if _is_geng_day(y, m, d):
                found += 1
                if found == count:
                    return (y, m, d)
            jd += 1.0

    xz_jd = gregorian_to_jd(xz.year, xz.month, float(xz.day))
    lq_jd = gregorian_to_jd(lq.year, lq.month, float(lq.day))

    # 初伏 = 3rd 庚日 on/after 夏至
    chu = next_geng_on_or_after(xz_jd, 3)
    # 中伏 = 4th 庚日 on/after 夏至
    zhong = next_geng_on_or_after(xz_jd, 4)
    # 末伏 = 1st 庚日 on/after 立秋
    mo = next_geng_on_or_after(lq_jd, 1)
    return {
        "初伏": chu,
        "中伏": zhong,
        "末伏": mo,
    }


def sanfu_on(year: int, month: int, day: int) -> Optional[str]:
    """If the date is in 三伏, return which period."""
    sf = sanfu_period(year)
    cur = (year, month, day)
    for name in ("初伏", "中伏", "末伏"):
        start = sf[name]
        # end: 10 days later (中伏 may be 20 days, but we just label by start)
        if start <= cur:
            # check it's before the next start
            others = [sf[n] for n in ("初伏", "中伏", "末伏") if n != name]
            if all(cur < o for o in others) or name == "末伏":
                # ensure within 10/20 days
                start_jd = gregorian_to_jd(*start)
                cur_jd = gregorian_to_jd(*cur)
                span = cur_jd - start_jd
                if 0 <= span <= 20:
                    return name
    return None


# ---------------------------------------------------------------------------
# Main festival lookup
# ---------------------------------------------------------------------------

def festivals_on(year: int, month: int, day: int) -> List[DayEvent]:
    """Return all events (festivals, solar terms, shujiu, sanfu) on a date."""
    out: List[DayEvent] = []
    # Modern festivals
    for m, d, zh, en in MODERN_FESTIVALS:
        if m == month and d == day:
            out.append(DayEvent(zh, en, "modern"))
    # Solar-term festivals (清明)
    from .solar import all_solar_terms
    for st in all_solar_terms(year):
        if (st.year, st.month, st.day) == (year, month, day):
            kind = "solar_term"
            out.append(DayEvent(st.name_zh, st.name_zh, kind))
    # Lunar festivals
    try:
        ld: LunarDate = solar_to_lunar(year, month, day)
    except Exception:
        ld = None
    if ld is not None:
        for lm, ld_, zh, en in TRADITIONAL_FESTIVALS:
            if ld.lunar_month == lm and ld.lunar_day == ld_ and not ld.is_leap:
                out.append(DayEvent(zh, en, "traditional"))
        # 除夕: last lunar day of the year.  We approximate: day after this is 正月初一.
        next_jd = gregorian_to_jd(year, month, float(day)) + 1.0
        ny, nm, nd = jd_to_gregorian(next_jd)
        nd = int(nd)
        try:
            nld = solar_to_lunar(ny, nm, nd)
            if nld.lunar_month == 1 and nld.lunar_day == 1:
                out.append(DayEvent("除夕", "New Year's Eve", "traditional"))
        except Exception:
            pass
    # Shujiu
    sj = shujiu_period(year, month, day)
    if sj is not None:
        out.append(DayEvent(f"{sj[0]}第{sj[1]}天", "Shujiu", "shujiu"))
    # Sanfu
    sf = sanfu_on(year, month, day)
    if sf is not None:
        out.append(DayEvent(sf, "Sanfu", "sanfu"))
    return out
