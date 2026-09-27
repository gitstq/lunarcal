# 🌙 lunarcal

[English](./README.md) | **简体中文** | [繁體中文](./README.zh-TW.md)

一个**零依赖、完全自研**的中国农历/历法引擎：既是 Python 库，也是命令行工具，原生面向 AI Agent 提供 JSON 结构化输出。

> 公历 ⇄ 农历互转 · 二十四节气精确到分钟 · 干支、生肖 · 传统与现代节日 · 数九、三伏 · 离线、确定性、无遥测。

---

## 🎉 项目介绍

日历、生日、节日、择期类应用，底层其实都卡在同一个无聊又致命的问题上：**需要一份正确的农历后端**。而市面上的方案要么塞了一坨黑盒数据表、要么依赖 C 扩展、要么把节气精确到哪一分钟这件事藏在一个"只给日期"的字符串背后。

**lunarcal** 从零自研，全部基于公开的天文算法文献（Meeus《Astronomical Algorithms》）：

- **太阳视黄经**由解析公式计算，再用二分法求出太阳黄经每跨过 15° 的那一刻——所以春分、冬至能给到**分钟级**时刻，而不是一个干巴巴的日期。
- **合朔（新月）时刻**由 Brown–Meeus 相位多项式加上主要周期差数计算；农历月即两个朔日之间的区间（北京时间）。
- **置闰**遵循经典的"无中气置闰"规则，以冬至所在月为十一月锚定。

代码 **100% 原创**：没有从 `lunar-python`、`cnlunar`、`sxtwl` 等任何现有农历库里复制代码或数据表；唯一"借用"的是公开的天文原理。支持年份范围 **1900 – 2100**，越界会抛出清晰错误。

灵感来源：每个做过节提醒的小项目，都曾经硬编码过"2024 年春节是 2 月 10 号"的痛苦。

---

## ✨ 核心特性

- ⚙️ **纯 Python 3.8+，仅标准库**——`pip install` 不装任何第三方包，无 numpy、无 ephem、无 C 扩展。
- 🕰️ **节气精确到分钟**（北京时间），通过太阳视黄经求根得到，不是查表。
- 🧮 **公历 ⇄ 农历**双向互转，正确处理闰月（如 2025 闰六月）。
- 🀄 **年柱、日柱干支**与**生肖**。
- 🏮 **传统节日**（春节/元宵/端午/七夕/中秋/重阳/腊八……）、**现代公历节日**、**除夕**。
- ❄️ **数九**（冬至起九九八十一天）与**三伏**（按夏至后第三个庚日起算，含初/中/末伏）。
- 🤖 **Agent 友好**：每个子命令都带 `--json`，输出形状稳定、确定，大模型无需额外提示即可解析。
- 🧪 **黄金值单元测试**——2020–2026 每年春节日期、全部目标闰月、关键节气日期全部锁定。
- 📦 同时发布 **wheel** 与**单文件 `lunarcal.pyz` zipapp**，任何有 Python 3.8+ 的机器都能直接跑。

---

## 🚀 快速开始

**环境要求：** Python 3.8 及以上（任意操作系统）。无运行时依赖。

```bash
# 从 PyPI 安装（发布后）
pip install lunarcal

# 或直接 clone 后安装
git clone https://github.com/gitstq/lunarcal.git
cd lunarcal
python3 -m pip install .

# 或者干脆不安装，直接跑单文件 zipapp
python3 lunarcal.pyz today
```

试一试：

```bash
lunarcal solar2lunar 2024-02-10
lunarcal terms 2024 --name 春分
lunarcal --json ganzhi 2024-02-10
```

---

## 📖 详细使用指南

### 命令行

```text
lunarcal [--json] <子命令> [参数]

  solar2lunar YYYY-MM-DD     公历转农历
  lunar2solar 年 月 日 [--leap]  农历转公历
  terms [年份] [--name 春分]  列出/查询节气
  ganzhi YYYY-MM-DD          年干支、日干支、生肖
  festival YYYY-MM-DD        当日节日、数九、三伏
  today                      今日全部信息（北京时间）
```

### `--json` 结构化输出（给 Agent 用）

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

### Python 库 API

```python
from lunarcal import solar_to_lunar, lunar_to_solar, solar_term_on

# 公历 -> 农历
ld = solar_to_lunar(2024, 2, 10)
print(ld.chinese_str())          # 2024年正月初一
print(ld.as_dict())

# 农历 -> 公历（含闰月）
print(lunar_to_solar(2025, 6, 1, is_leap=True))   # (2025, 7, 25)

# 节气精确到分钟
st = solar_term_on(2024, "春分")
print(f"{st.year}-{st.month:02d}-{st.day:02d} {st.hour:02d}:{st.minute:02d}")
# 2024-03-20 11:03
```

### 典型使用场景

- 生日/纪念日提醒：存农历生日，每年自动换算成公历。
- 每日早报 Bot：早上 8 点播报"今日大寒 / 四九第三天"。
- 预约小程序：把清明、端午、中秋这些传统节日自动置灰。
- LLM Agent：用户随口问个日期问题，Agent 调一下 `lunarcal --json …`，直接在稳定 JSON 上做推理。

> 🖼️ *终端录屏 / 演示动图将放在这里。*

---

## 💡 设计思路与迭代规划

**为什么要解析算太阳黄经，而不是塞一张查表？**
对 1900–2100 来说，预计算表当然也能跑，但那样项目就退化成了"数据表解析器"。对视太阳黄经（Meeus 第 25 章低精度序列 + 章动/光行差）求根，零数据体积就能给到分钟级精度，将来要扩年份范围也不用改表。

**为什么要从头算合朔？**
Meeus 第 47 章相位多项式加上主要周期差数，在 1900–2100 范围内把朔日时刻复现到几分钟误差——足够把每个农历月的边界钉死在正确的北京时间上。之后"冬至后第一个无中气之月为闰月"的规则就纯粹是簿记问题。

**后续迭代：**
- 月柱、日柱之外的八字四柱（目前有年柱、日柱）。
- 二十八宿、建除十二神等更丰富的老黄历输出。
- 可选时区覆盖（当前固定 Asia/Shanghai）。
- 给 IDE 用户加类型存根（`py.typed`）。
- 可选的 Rust / PyO3 加速内核（保留在默认零依赖路径之外）。

欢迎参与共建，详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

---

## 📦 打包与部署指南

```bash
# 作为库 + 命令行工具安装
python3 -m pip install .
lunarcal today

# 打 wheel（build 仅为开发依赖）
python3 -m pip install build
python3 -m build --wheel
ls dist/lunarcal-0.1.0-py3-none-any.whl

# 打单文件 zipapp（无需安装）
python3 scripts/build_zipapp.py
python3 lunarcal.pyz today
./lunarcal.pyz solar2lunar 2026-02-17
```

兼容环境：CPython 3.8 / 3.9 / 3.10 / 3.11 / 3.12，Linux / macOS / Windows。**无任何运行时依赖**；`build` 仅用于打 wheel。

---

## 🤝 贡献指南

欢迎提 PR，请：

1. 任何行为改动都配套新增/更新黄金值测试。
2. 跑 `make test` 保持全绿。
3. 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)：`feat:` / `fix:` / `docs:` / `refactor:` / `test:` / `chore:`。

提 Issue 时请附上：北京时间日期、lunarcal 实际输出、正确值应为多少（最好给出处）。

---

## 📄 开源协议

MIT——详见 [LICENSE](./LICENSE)。© 2026 gitstq。
