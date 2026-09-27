# 🌙 lunarcal

[English](./README.md) | [简体中文](./README.zh-CN.md) | **繁體中文**

一個**零相依、完全自行研發**的中國農曆／曆法引擎：同時提供 Python 函式庫與命令列工具，原生為 AI Agent 輸出 JSON 結構化資料。

> 國曆 ⇄ 農曆雙向轉換 · 二十四節氣精算至分鐘 · 干支、生肖 · 傳統與現代節日 · 數九、三伏 · 離線、確定性、無遙測。

---

## 🎉 專案介紹

日曆、生日、節日、擇日這類應用，底層其實都卡在同一個無趣卻致命的問題上：**需要一份正確的農曆後端**。而坊間常見的方案，不是塞了一大包黑箱資料表、就是依賴 C 擴充套件，不然就是把「節氣到底是哪一分鐘」這件事，藏在一個只給日期的字串背後。

**lunarcal** 從零開始自行研發，全部奠基於公開的天文演算法文獻（Meeus《Astronomical Algorithms》）：

- **太陽視黃經**以解析公式計算，再用二分法求出太陽黃經每跨過 15° 的那一刻——所以春分、冬至能精算到**分鐘**，而不只是一個乾扁扁的日期。
- **合朔（新月）時刻**由 Brown–Meeus 相位多項式搭配主要週期差數算出；一個農曆月就是兩個朔日之間的區間（北京地方標準時間）。
- **置閏**遵循經典的「無中氣則閏」規則，以冬至所在月為十一月錨定。

程式碼 **100% 原創**：未從 `lunar-python`、`cnlunar`、`sxtwl` 等任何現有農曆函式庫抄襲程式碼或資料表；唯一「引用」的是公開的天文原理。支援年份範圍 **1900 – 2100**，超出範圍會丟出明確錯誤。

靈感來源：每一個做過節日提醒的小專案，都曾經硬編碼過「2024 年春節是 2 月 10 號」的痛苦。

---

## ✨ 核心特性

- ⚙️ **純 Python 3.8+，僅標準函式庫**——`pip install` 不拉入任何第三方套件，無 numpy、無 ephem、無 C 擴充。
- 🕰️ **節氣精算至分鐘**（北京時間），透過太陽視黃經求根，不是查表。
- 🧮 **國曆 ⇄ 農曆**雙向轉換，正確處理閏月（例如 2025 年閏六月）。
- 🀄 **年柱、日柱干支**與**生肖**。
- 🏮 **傳統節日**（春節／元宵／端午／七夕／中秋／重陽／臘八……）、**現代國定假日**、**除夕**。
- ❄️ **數九**（冬至起九九八十一天）與**三伏**（依夏至後第三個庚日起算，含初伏／中伏／末伏）。
- 🤖 **Agent 友善**：每個子指令都附 `--json`，輸出形狀穩定、確定性高，大模型不需額外提示即可剖析。
- 🧪 **黃金值單元測試**——2020–2026 每年春節日期、所有目標閏月、關鍵節氣日期全部鎖定。
- 📦 同時釋出 **wheel** 與**單一檔案 `lunarcal.pyz` zipapp**，任何有 Python 3.8+ 的機器都能直接執行。

---

## 🚀 快速開始

**環境需求：** Python 3.8 以上（任何作業系統）。無執行期相依套件。

```bash
# 從 PyPI 安裝（釋出後）
pip install lunarcal

# 或直接 clone 後安裝
git clone https://github.com/gitstq/lunarcal.git
cd lunarcal
python3 -m pip install .

# 或根本不安裝，直接跑單一檔案 zipapp
python3 lunarcal.pyz today
```

試試看：

```bash
lunarcal solar2lunar 2024-02-10
lunarcal terms 2024 --name 春分
lunarcal --json ganzhi 2024-02-10
```

---

## 📖 詳細使用指南

### 命令列

```text
lunarcal [--json] <子指令> [參數]

  solar2lunar YYYY-MM-DD     國曆轉農曆
  lunar2solar 年 月 日 [--leap]  農曆轉國曆
  terms [年份] [--name 春分]  列出／查詢節氣
  ganzhi YYYY-MM-DD          年干支、日干支、生肖
  festival YYYY-MM-DD        當日節日、數九、三伏
  today                      今日完整資訊（北京時間）
```

### `--json` 結構化輸出（給 Agent 用）

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

### Python 函式庫 API

```python
from lunarcal import solar_to_lunar, lunar_to_solar, solar_term_on

# 國曆 -> 農曆
ld = solar_to_lunar(2024, 2, 10)
print(ld.chinese_str())          # 2024年正月初一
print(ld.as_dict())

# 農曆 -> 國曆（含閏月）
print(lunar_to_solar(2025, 6, 1, is_leap=True))   # (2025, 7, 25)

# 節氣精算至分鐘
st = solar_term_on(2024, "春分")
print(f"{st.year}-{st.month:02d}-{st.day:02d} {st.hour:02d}:{st.minute:02d}")
# 2024-03-20 11:03
```

### 典型使用情境

- 生日／紀念日提醒：存農曆生日，每年自動換算成國曆。
- 每日早報 Bot：早上 8 點播報「今日大寒／四九第三天」。
- 預約小程式：把清明、端午、中秋這些傳統節日自動灰階。
- LLM Agent：使用者隨口問個日期問題，Agent 呼叫 `lunarcal --json …`，直接在穩定 JSON 上推理。

> 🖼️ *終端錄影／示範 GIF 將放在這裡。*

---

## 💡 設計思路與迭代規劃

**為什麼要解析計算太陽黃經，而不是塞一張查表？**
對 1900–2100 來說，預先計算的查表當然也能跑，但那樣專案就退化成「資料表解析器」了。對視太陽黃經（Meeus 第 25 章低精度序列＋章動／光行差）求根，零資料體積就能給到分鐘級精度，將來要擴年份範圍也不用改表。

**為什麼要從頭算合朔？**
Meeus 第 47 章相位多項式加上主要週期差數，在 1900–2100 範圍內把朔日時刻重現到幾分鐘誤差——足夠把每個農曆月的邊界釘在正確的北京時間上。之後「冬至後第一個無中氣之月為閏月」的規則就單純是簿記問題。

**後續迭代：**
- 月柱、時柱等八字四柱（目前已有年柱、日柱）。
- 二十八宿、建除十二神等更豐富的老黃曆輸出。
- 可選時區覆寫（目前固定 Asia/Shanghai）。
- 給 IDE 使用者加上型別存根（`py.typed`）。
- 可選的 Rust／PyO3 加速核心（保留在預設零相依路徑之外）。

歡迎參與共建，詳見 [CONTRIBUTING.md](./CONTRIBUTING.md)。

---

## 📦 打包與部署指南

```bash
# 做為函式庫＋命令列工具安裝
python3 -m pip install .
lunarcal today

# 打 wheel（build 僅為開發相依）
python3 -m pip install build
python3 -m build --wheel
ls dist/lunarcal-0.1.0-py3-none-any.whl

# 打單一檔案 zipapp（免安裝）
python3 scripts/build_zipapp.py
python3 lunarcal.pyz today
./lunarcal.pyz solar2lunar 2026-02-17
```

相容環境：CPython 3.8／3.9／3.10／3.11／3.12，Linux／macOS／Windows。**無任何執行期相依套件**；`build` 僅用於打包 wheel。

---

## 🤝 貢獻指南

歡迎發 PR，請：

1. 任何行為變動都要配套新增／更新黃金值測試。
2. 跑 `make test` 保持全綠。
3. 提交訊息遵循 [Conventional Commits](https://www.conventionalcommits.org/)：`feat:`／`fix:`／`docs:`／`refactor:`／`test:`／`chore:`。

回報 Issue 時請附上：北京時間日期、lunarcal 實際輸出、正確值應為何（最好附出處）。

---

## 📄 開源協議

MIT——詳見 [LICENSE](./LICENSE)。© 2026 gitstq。
