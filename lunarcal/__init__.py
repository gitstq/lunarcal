"""lunarcal -- a zero-dependency Chinese lunar-calendar engine.

Public API
==========
- :class:`~lunarcal.lunar.LunarDate` and :func:`solar_to_lunar` /
  :func:`lunar_to_solar` for Gregorian <-> lunar conversion.
- :func:`~lunarcal.solar.solar_term_on` and :func:`~lunarcal.solar.all_solar_terms`
  for 24 solar terms precise to the minute.
- :func:`~lunarcal.ganzhi.year_ganzhi_str` / :func:`~lunarcal.ganzhi.day_ganzhi_str`
  and :func:`~lunarcal.ganzhi.zodiac_year`.
- :func:`~lunarcal.festival.festivals_on`, :func:`~lunarcal.festival.shujiu_period`,
  :func:`~lunarcal.festival.sanfu_period`.
"""

from .lunar import (
    LunarDate,
    LunarRangeError,
    solar_to_lunar,
    lunar_to_solar,
    leap_month_of_year,
    YEAR_MIN,
    YEAR_MAX,
)
from .solar import SolarTerm, solar_term_on, all_solar_terms, SOLAR_TERMS_ZH
from .ganzhi import (
    year_ganzhi_str,
    day_ganzhi_str,
    zodiac_year,
    STEMS,
    BRANCHES,
    ZODIAC,
)
from .festival import (
    festivals_on,
    shujiu_period,
    sanfu_period,
    sanfu_on,
    DayEvent,
    TRADITIONAL_FESTIVALS,
    MODERN_FESTIVALS,
)

__version__ = "0.1.0"
__all__ = [
    "LunarDate",
    "LunarRangeError",
    "solar_to_lunar",
    "lunar_to_solar",
    "leap_month_of_year",
    "YEAR_MIN",
    "YEAR_MAX",
    "SolarTerm",
    "solar_term_on",
    "all_solar_terms",
    "SOLAR_TERMS_ZH",
    "year_ganzhi_str",
    "day_ganzhi_str",
    "zodiac_year",
    "STEMS",
    "BRANCHES",
    "ZODIAC",
    "festivals_on",
    "shujiu_period",
    "sanfu_period",
    "sanfu_on",
    "DayEvent",
    "TRADITIONAL_FESTIVALS",
    "MODERN_FESTIVALS",
    "__version__",
]
