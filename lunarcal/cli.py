"""Command-line interface for lunarcal.

Subcommands
-----------
- `solar2lunar YYYY-MM-DD`   Gregorian -> lunar
- `lunar2solar YYYY M D [--leap]`   lunar -> Gregorian
- `terms [YEAR] [--name 春分]`   solar terms
- `ganzhi YYYY-MM-DD`        year/day ganzhi + zodiac
- `festival YYYY-MM-DD`      festivals / shujiu / sanfu on a date
- `today`                    all info for today (Beijing)

Global flag `--json` emits structured JSON instead of human-readable text.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from . import (
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
    __version__,
)

BJT = timezone(timedelta(hours=8))


def _parse_date(s: str) -> tuple:
    s = s.strip()
    for sep in ("-", "/", "."):
        if sep in s:
            y, m, d = s.split(sep)
            return int(y), int(m), int(d)
    if len(s) == 8 and s.isdigit():
        return int(s[:4]), int(s[4:6]), int(s[6:8])
    raise ValueError(f"Cannot parse date: {s!r} (use YYYY-MM-DD)")


def _today_bjt() -> tuple:
    now = datetime.now(BJT)
    return now.year, now.month, now.day


def cmd_solar2lunar(args) -> int:
    y, m, d = _parse_date(args.date)
    ld = solar_to_lunar(y, m, d)
    if args.json:
        print(json.dumps(ld.as_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"公历 {y:04d}-{m:02d}-{d:02d}")
        print(f"农历 {ld.chinese_str()}  ({ld.lunar_year}年{ld.month_name()}{ld.day_name()})")
        print(f"干支年 {year_ganzhi_str(ld.lunar_year)}  生肖 {zodiac_year(ld.lunar_year)}")
        print(f"日干支 {day_ganzhi_str(y, m, d)}")
    return 0


def cmd_lunar2solar(args) -> int:
    y, m, d = args.year, args.month, args.day
    gy, gm, gd = lunar_to_solar(y, m, d, is_leap=args.leap)
    if args.json:
        print(json.dumps({
            "lunar_year": y, "lunar_month": m, "lunar_day": d, "is_leap": args.leap,
            "gregorian": f"{gy:04d}-{gm:02d}-{gd:02d}",
        }, ensure_ascii=False, indent=2))
    else:
        tag = "闰" if args.leap else ""
        print(f"农历 {y}年{tag}{m}月{d}日 -> 公历 {gy:04d}-{gm:02d}-{gd:02d}")
    return 0


def cmd_terms(args) -> int:
    year = args.year or datetime.now(BJT).year
    if args.name:
        st = solar_term_on(year, args.name)
        items = [st]
    else:
        items = all_solar_terms(year)
    if args.json:
        print(json.dumps([s.as_dict() for s in items], ensure_ascii=False, indent=2))
    else:
        for st in items:
            print(f"{st.name_zh:>4s}  太阳黄经 {st.longitude_deg:6.1f}°  "
                  f"{st.year:04d}-{st.month:02d}-{st.day:02d} {st.hour:02d}:{st.minute:02d} (北京)")
    return 0


def cmd_ganzhi(args) -> int:
    y, m, d = _parse_date(args.date)
    if args.json:
        print(json.dumps({
            "date": f"{y:04d}-{m:02d}-{d:02d}",
            "year_ganzhi": year_ganzhi_str(y),
            "day_ganzhi": day_ganzhi_str(y, m, d),
            "zodiac": zodiac_year(y),
        }, ensure_ascii=False, indent=2))
    else:
        print(f"公历 {y:04d}-{m:02d}-{d:02d}")
        print(f"年干支 {year_ganzhi_str(y)}  生肖 {zodiac_year(y)}")
        print(f"日干支 {day_ganzhi_str(y, m, d)}")
    return 0


def cmd_festival(args) -> int:
    y, m, d = _parse_date(args.date)
    evs = festivals_on(y, m, d)
    sj = shujiu_period(y, m, d)
    sf = sanfu_period(y)
    if args.json:
        payload = {
            "date": f"{y:04d}-{m:02d}-{d:02d}",
            "events": [e.as_dict() for e in evs],
            "shujiu": {"period": sj[0], "day": sj[1]} if sj else None,
            "sanfu_this_year": {
                k: f"{v[0]:04d}-{v[1]:02d}-{v[2]:02d}" for k, v in sf.items()
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"公历 {y:04d}-{m:02d}-{d:02d}")
        if evs:
            for e in evs:
                print(f"  [{e.kind}] {e.name_zh} ({e.name_en})")
        else:
            print("  (无节日)")
        if sj:
            print(f"数九: {sj[0]} 第{sj[1]}天")
        print("三伏:")
        for k, v in sf.items():
            print(f"  {k}: {v[0]:04d}-{v[1]:02d}-{v[2]:02d}")
    return 0


def cmd_today(args) -> int:
    y, m, d = _today_bjt()
    args.date = f"{y:04d}-{m:02d}-{d:02d}"
    rc1 = cmd_solar2lunar(args)
    print()
    rc2 = cmd_festival(args)
    return rc1 or rc2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lunarcal",
        description="零依赖中国农历/历法引擎 (Python 3.8+, 标准库 only).",
    )
    p.add_argument("--version", action="version", version=f"lunarcal {__version__}")
    p.add_argument("--json", action="store_true", help="emit structured JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("solar2lunar", help="公历转农历")
    sp.add_argument("date", help="YYYY-MM-DD")
    sp.set_defaults(func=cmd_solar2lunar)

    sp = sub.add_parser("lunar2solar", help="农历转公历")
    sp.add_argument("year", type=int)
    sp.add_argument("month", type=int)
    sp.add_argument("day", type=int)
    sp.add_argument("--leap", action="store_true", help="is leap month")
    sp.set_defaults(func=cmd_lunar2solar)

    sp = sub.add_parser("terms", help="二十四节气")
    sp.add_argument("year", type=int, nargs="?")
    sp.add_argument("--name", help="e.g. 春分")
    sp.set_defaults(func=cmd_terms)

    sp = sub.add_parser("ganzhi", help="干支/生肖")
    sp.add_argument("date", help="YYYY-MM-DD")
    sp.set_defaults(func=cmd_ganzhi)

    sp = sub.add_parser("festival", help="节日/数九/三伏")
    sp.add_argument("date", help="YYYY-MM-DD")
    sp.set_defaults(func=cmd_festival)

    sp = sub.add_parser("today", help="今日全部信息")
    sp.set_defaults(func=cmd_today)
    return p


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except LunarRangeError as e:
        print(f"lunarcal: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"lunarcal: error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
