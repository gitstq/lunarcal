# 🌙 lunarcal

**English** | [简体中文](./README.zh-CN.md) | [繁體中文](./README.zh-TW.md)

A **zero-dependency, self-implemented Chinese lunar-calendar engine** for Python — both a library and a CLI, designed to be called directly by AI agents with structured JSON output.

> Gregorian ⇄ lunar conversion · 24 solar terms to the minute · stems & branches · zodiac · traditional & modern festivals · 数九 / 三伏 · offline, deterministic, no telemetry.

---

## 🎉 Introduction

Calendar, birthday, festival and date-selection apps all share the same boring problem: they need a *correct* Chinese-calendar backend, and every existing option either ships a huge opaque data table, depends on C extensions, or hides the exact instant of a solar term behind a date-only string.

**lunarcal** is built from scratch on top of the public astronomical-algorithm literature (Meeus, *Astronomical Algorithms*):

- **Sun apparent ecliptic longitude** is computed analytically, and the instant the Sun crosses each 15° meridian is solved by bisection — so 春分 / 冬至 come out to the **minute**, not just the date.
- **New moons** are computed from the Brown–Meeus phase polynomial plus the dominant periodic inequalities; a lunar month is the interval between two new moons (Beijing civil time).
- **Leap months** follow the classical *no-major-zhongqi → leap* rule, anchored on the winter solstice.

It is **100% original code**: no data tables copied from `lunar-python`, `cnlunar`, `sxtwl` or any other library. The only "borrowed" idea is the well-known astronomy. Supported range: **1900 – 2100**; out-of-range dates raise a clear error.

Inspiration: the quiet frustration of every side-project that has ever hard-coded "CNY 2024 is Feb 10".

---

## ✨ Features

- ⚙️ **Pure Python 3.8+, standard library only** — `pip install` pulls in *nothing*. No `numpy`, no `ephem`, no C extensions.
- 🕰️ **Solar terms to the minute** (Beijing time), via root-finding on apparent solar longitude — not date lookup.
- 🧮 **Gregorian ⇄ lunar** both directions, including leap months (e.g. 2025 闰六月).
- 🀄 **干支 (Heavenly Stems / Earthly Branches)** for year and day, plus the **生肖 zodiac**.
- 🏮 **Traditional festivals** (春节 / 元宵 / 端午 / 七夕 / 中秋 / 重阳 / 腊八 …), **modern public holidays**, and **除夕**.
- ❄️ **数九** (the 9×9 cold period starting at 冬至) and **三伏** (初伏 / 中伏 / 末伏 by the 庚-day rule).
- 🤖 **Agent-native**: every subcommand has a `--json` flag that emits deterministic, stable-shape output an LLM can parse without prompting.
- 🧪 **Golden-value unit tests** — every CNY date 2020–2026, every target leap month, and every key solar-term date is locked in.
- 📦 Ships as a **wheel** *and* a **single-file `lunarcal.pyz` zipapp** — run anywhere Python 3.8+ exists.

---

## 🚀 Quick start

**Requirements:** Python 3.8 or newer (any OS). No runtime dependencies.

```bash
# From PyPI (when published)
pip install lunarcal

# Or straight from a clone
git clone https://github.com/gitstq/lunarcal.git
cd lunarcal
python3 -m pip install .

# Or run the single-file zipapp with no install at all
python3 lunarcal.pyz today
```

Try it:

```bash
lunarcal solar2lunar 2024-02-10
lunarcal terms 2024 --name 春分
lunarcal --json ganzhi 2024-02-10
```

---

## 📖 Detailed usage

### CLI

```text
lunarcal [--json] <subcommand> [args]

  solar2lunar YYYY-MM-DD     Gregorian → lunar
  lunar2solar Y M D [--leap] lunar → Gregorian
  terms [YEAR] [--name 春分] list / query solar terms
  ganzhi YYYY-MM-DD          year & day stems-branches, zodiac
  festival YYYY-MM-DD        festivals, 数九, 三伏 on a date
  today                      everything for today (Beijing)
```

### `--json` output (agent-native)

```bash
$ lunarcal --json solar2lunar 2024-02-10
{
  "lunar_year": 2024,
  "lunar_month": 1,
  "lunar_day": 1,
  "is_leap": false,
  "month_name_zh": "正月",
  "day_name_zh": "初一",
  "gregorian": "2024-02-10"
}
```

```bash
$ lunarcal --json terms 2024 --name 冬至
[
  {
    "name_zh": "冬至",
    "longitude_deg": 270.0,
    "beijing": "2024-12-21 17:13"
  }
]
```

### Python library

```python
from lunarcal import solar_to_lunar, lunar_to_solar, solar_term_on

# Gregorian -> lunar
ld = solar_to_lunar(2024, 2, 10)
print(ld.chinese_str())          # 2024年正月初一
print(ld.as_dict())

# Lunar -> Gregorian (leap month)
print(lunar_to_solar(2025, 6, 1, is_leap=True))   # (2025, 7, 25)

# Solar term to the minute
st = solar_term_on(2024, "春分")
print(st.beijing if hasattr(st, "beijing") else
      f"{st.year}-{st.month:02d}-{st.day:02d} {st.hour:02d}:{st.minute:02d}")
# 2024-03-20 11:03
```

### Typical scenarios

- A birthday/anniversary reminder that stores the lunar birthday and shows the Gregorian date each year.
- A bot that posts "今日 大寒 / 四九第三天" at 08:00 Beijing.
- A booking widget that greys out 清明节 / 端午节 / 中秋节.
- An LLM agent that, given a free-form date question, calls `lunarcal --json …` and reasons over stable JSON.

> 🖼️ *Terminal recording / demo GIF will go here.*

---

## 💡 Design notes & roadmap

**Why compute solar longitude analytically instead of shipping a table?**
A precomputed table is fine for 1900–2100, but it makes the project a "data parser" rather than an engine. Root-finding on the apparent Sun's ecliptic longitude (Meeus Ch. 25 low-accuracy series + nutation/aberration) gives minute-level accuracy with zero bundled data, and stays correct if you ever widen the year range.

**Why solve new moons from first principles?**
The Meeus Ch. 47 phase polynomial plus the dominant periodic inequalities reproduces the new-moon instants to within a few minutes over 1900–2100 — enough to pin every lunar-month boundary on the correct Beijing date. The leap-month rule ("first post-冬至 month with no 中气 is the leap month") is then applied purely by bookkeeping.

**Roadmap:**
- Month-/day-level 干支 (八字 pillars) beyond year & day.
- 二十八宿 and 建除十二神 for richer almanac output.
- Optional timezone override (currently fixed to Asia/Shanghai).
- Type stubs (`py.typed`) for IDE users.
- Rust core / PyO3 optional acceleration (kept *out* of the default zero-dep path).

**Contributions welcome** — see [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## 📦 Packaging & deployment

```bash
# Install as a library + console script
python3 -m pip install .
lunarcal today

# Build a wheel (build is a DEV-only dependency)
python3 -m pip install build
python3 -m build --wheel
ls dist/lunarcal-0.1.0-py3-none-any.whl

# Build the single-file zipapp (no install needed)
python3 scripts/build_zipapp.py
python3 lunarcal.pyz today
./lunarcal.pyz solar2lunar 2026-02-17
```

Compatibility: CPython 3.8, 3.9, 3.10, 3.11, 3.12 on Linux / macOS / Windows. There are **no runtime dependencies**; `build` is used only to produce wheels.

---

## 🤝 Contributing

PRs are welcome. Please:

1. Add or update golden-value tests for any behaviour change.
2. Run `make test` and keep it green.
3. Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

Issues: include the Beijing date, what lunarcal returned, and what the correct value should be.

---

## 📄 License

MIT — see [LICENSE](./LICENSE). © 2026 gitstq.
