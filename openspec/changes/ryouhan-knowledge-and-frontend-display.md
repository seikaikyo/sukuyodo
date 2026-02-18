---
title: 凌犯知識補完與前端新欄位呈現
type: feature
status: completed
created: 2026-02-18
---

# 凌犯知識補完與前端新欄位呈現

## 背景

後端經兩輪稽核後，凌犯期間的計算邏輯已正確，compound_analysis / effective_interpretation / week_warnings / month_warnings 等欄位也已回傳。但存在兩個面向的缺口：

1. **知識面**：凌犯期間的描述文字缺乏三語（漢文原典/日文/正體中文）、出處引用、公式計算說明
2. **前端面**：12 個後端新增欄位完全未在前端呈現

## 變更內容

### Part A: 後端凌犯知識補完

#### A1. ryouhan 回傳物件結構化

現有回傳只有一個混合語言的 `description` 欄位，改為結構化三語：

```python
return {
    "active": True,
    "lunar_month": lunar_m,
    "start_day": start_day,
    "end_day": end_day,
    "weekday_name": weekday_name,        # 朔日七曜名（如「土曜」）
    "period_label": period_label,         # 可讀標籤（如「正月土曜期」）
    "description": "...",                 # 正體中文（維持既有欄位名）
    "description_ja": "...",              # 日文
    "description_classic": "...",         # 漢文原典
    "source": "宿曜經卷五・七曜陵逼",     # 出處
    "formula": {                          # 計算公式說明
        "step1": "西曆→農曆轉換",
        "step2": "取朔日（農曆初一）的七曜",
        "step3": "查 RYOUHAN_MAP[(農曆月, 朔日七曜)]",
        "step4": "判定當日農曆日是否在 [start_day, end_day] 區間"
    }
}
```

#### A2. RYOUHAN_DESCRIPTIONS 三語描述資料

新增常數，為 12 個農曆月各提供三語描述模板：

```python
RYOUHAN_DESCRIPTIONS = {
    1: {
        "classic": "正月土曜朔日，初一至十六日陵逼。日曜朔日，十七至三十日陵逼。",
        "ja": "正月の朔日が土曜の場合は1日〜16日、日曜の場合は17日〜30日が凌犯期間。",
        "zh": "正月朔日為土曜，初一至十六為凌犯期間；朔日為日曜，十七至三十為凌犯期間。"
    },
    # ... 12 個月
}
```

#### A3. RYOUHAN_CATEGORY_DESCRIPTIONS 補日文版

現有 career/love/health/wealth 各 3 級只有中文，補 `_ja` 版本。

### Part B: 前端新欄位呈現

#### B1. TypeScript interface 更新（useSukuyodo.ts）

更新以下 interface：

- `FortuneScores`: 加 `effective_interpretation`, `ryouhan_active`, `ryouhan_warning`, `ryouhan_warning_ja`
- `DailyFortune`: 加 `compound_analysis`
- `WeeklyFortune`: 加 `week_warnings`; `daily_overview[]` 加 `special_day`, `ryouhan_active`, `is_dark_week`
- `MonthlyFortune`: 加 `month_warnings`, `ryouhan_info`, `special_days`; `weekly[].warnings`

#### B2. 今日頁籤 — compound_analysis 顯示

在日運詳情區最上方，若有 compound_analysis 則顯示：
- 高嚴重度（severity >= 4）用警告色背景
- 顯示 name + description
- 凌犯相關的 compound 用紅色系

#### B3. 今日頁籤 — ryouhan_warning 橫幅

凌犯期間時，在分數卡片上方顯示警告橫幅：
- 背景色：暗紅/橘
- 文字：ryouhan_warning（中文優先，可切換日文）

#### B4. 本週/本月 daily chip 增強

daily_overview chip 上增加視覺標記：
- `ryouhan_active` → chip 加紅色邊框
- `special_day` → chip 下方小文字（甘/金/羅）
- `is_dark_week` → chip 加灰底

#### B5. 本月 — month_warnings / ryouhan_info 顯示

月運頁籤頂部增加警告區：
- month_warnings 列表顯示
- ryouhan_info 顯示「本月 X 天處於凌犯期間」

#### B6. 本週 — week_warnings 顯示

週運詳情中顯示 week_warnings 列表。

## 影響範圍

| 檔案 | 修改內容 |
|------|---------|
| `backend/services/sukuyodo.py` | ryouhan 回傳結構化、RYOUHAN_DESCRIPTIONS 三語、RYOUHAN_CATEGORY_DESCRIPTIONS 補日文 |
| `frontend/src/composables/useSukuyodo.ts` | interface 更新 |
| `frontend/src/components/FortuneTab.vue` | compound_analysis/warnings/chip 增強 |

## 不修改的部分

- 凌犯計算邏輯（已正確）
- 月曆元件（FortuneCalendar.vue 已正確使用 ryouhan/special_day）
- 相性/九曜計算

## 測試計畫

1. 凌犯日（7/19）→ ryouhan 物件有三語描述 + source + formula
2. 非凌犯日 → ryouhan 為 null，無警告橫幅
3. compound_analysis 顯示（2/23 triple_auspicious / 7/7 ryouhan_trap）
4. daily chip 紅框（凌犯日）、灰底（暗黒）、小標（甘露/羅刹）
5. month_warnings / week_warnings 顯示
6. vue-tsc --noEmit 和 vite build 通過

## Checklist

- [ ] A1: ryouhan 回傳物件結構化（三語 + source + formula）
- [ ] A2: RYOUHAN_DESCRIPTIONS 12 月三語描述
- [ ] A3: RYOUHAN_CATEGORY_DESCRIPTIONS 補日文版
- [ ] B1: TypeScript interface 更新
- [ ] B2: compound_analysis 顯示
- [ ] B3: ryouhan_warning 橫幅
- [ ] B4: daily chip 增強（凌犯/暗黒/特殊日標記）
- [ ] B5: month_warnings / ryouhan_info 顯示
- [ ] B6: week_warnings 顯示
- [ ] 建構驗證通過
