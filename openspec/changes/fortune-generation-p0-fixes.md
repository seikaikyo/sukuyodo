---
title: 運勢生成 P0 修正 — 消除隨機數、補凌犯/特殊日
type: fix
status: completed
created: 2026-02-18
---

# 運勢生成 P0 修正

## 背景

經完整稽核後發現，日運（`calculate_daily_fortune`）已正確處理凌犯期間、甘露日/羅刹日/金剛峯日、六害宿、暗黒の一週間等所有因素。但月運、週運、年運三個層級存在嚴重脫節：用隨機數填充分數、忽略凌犯期間、不彙報特殊日資訊。

結果是使用者在「年→月→週」的瀏覽路徑中看到的分數與實際日運完全脫鉤，造成誤判。

## 問題清單

### P0-1: 年運 monthly_trend 使用 random.randint 產生假分數

**位置**: `sukuyodo.py` 第 2734-2742 行

```python
# 現況：隨機產生 12 個月分數
random.seed(f"{birth_date.isoformat()}{year}")
for m in range(1, 13):
    month_score = max(40, min(100, base_score + random.randint(-20, 20)))
```

**問題**: 每月分數和實際月宿關係、凌犯期間完全無關，純粹是亂數。

**修正方案**: 改為呼叫月宿計算邏輯，取得本命宿 vs 該月月宿的關係分數，再疊加該月是否有凌犯期間。

### P0-2: 月運完全忽略凌犯期間

**位置**: `sukuyodo.py` `calculate_monthly_fortune()` 第 1822-1957 行

**問題**: 月運已正確計算月宿關係和基礎分數，但從未呼叫 `check_ryouhan_period()`。若該月處於凌犯期間，分數和描述完全不反映此事。

**修正方案**: 掃描該月所有日期，偵測凌犯期間天數比例，依比例調整月整體分數並加入 `ryouhan_info` 欄位。

### P0-3: 週運/月運不彙報特殊日資訊

**位置**: `sukuyodo.py` `calculate_weekly_fortune()` 第 2022-2033 行、`calculate_monthly_fortune()` 第 1896-1913 行

**問題**: 兩者都已對每日呼叫 `calculate_daily_fortune()` 取得完整日運，但 daily_overview 只擷取 `date/weekday/score`，丟棄了凌犯、特殊日、六害宿、暗黒の一週間等資訊。

**修正方案**: daily_overview 補充 `special_day`（甘露/金剛峯/羅刹）、`ryouhan_active`、`is_dark_week` 欄位。週運和月運層級彙整這些資訊，產生 `week_warnings` / `month_warnings` 摘要。

## 影響範圍

| 檔案 | 修改內容 |
|------|---------|
| `backend/services/sukuyodo.py` | 三處修正（年運 monthly_trend、月運凌犯偵測、週/月 daily_overview 補充） |

僅修改後端一個檔案，前端已有展開顯示能力，新增欄位自動呈現。

## 技術設計

### P0-1 年運 monthly_trend 改造

```python
monthly_trend = []
for m in range(1, 13):
    # 取得該月月宿
    mid_date = date(year, m, 15)
    _, lunar_month, _, _ = self.solar_to_lunar(mid_date)
    month_mansion_idx = self.MONTH_START_MANSION.get(lunar_month, 0)

    # 本命宿 vs 月宿關係
    relation = self.get_relation_type(user_index, month_mansion_idx)
    month_score = relation["score"]

    # 九曜星元素加成
    if star_element:
        _, star_bonus_monthly = self._calc_fortune_element_relation(
            self.mansions_data[month_mansion_idx]["element"], star_element
        )
        month_score += star_bonus_monthly // 4

    # 凌犯期間偵測（抽樣該月 1/8/15/22 日）
    ryouhan_days = 0
    sample_dates = [date(year, m, d) for d in [1, 8, 15, 22] if d <= days_in_month]
    for sd in sample_dates:
        ryouhan = self.check_ryouhan_period(sd, user_index)
        if ryouhan:
            ryouhan_days += 1
    if ryouhan_days > 0:
        month_score = max(40, month_score - ryouhan_days * 5)

    month_score = max(40, min(100, month_score))
    monthly_trend.append({
        "month": m,
        "score": month_score,
        "ryouhan_ratio": ryouhan_days / len(sample_dates) if sample_dates else 0
    })
```

### P0-2 月運凌犯偵測

在 `calculate_monthly_fortune()` 中，遍歷每日時順帶記錄凌犯天數：

```python
# 在 daily_overview 迴圈中累計
ryouhan_count = 0
special_days_in_month = []
dark_week_count = 0

for d in range(week_end_offset - day_offset + 1):
    day_date = week_start + timedelta(days=d)
    daily_fortune = self.calculate_daily_fortune(birth_date, day_date)

    # 擷取更多資訊
    is_ryouhan = daily_fortune.get("ryouhan", {}).get("active", False)
    special_day = daily_fortune.get("special_day")
    is_dark = daily_fortune.get("sanki", {}).get("is_dark_week", False)

    if is_ryouhan: ryouhan_count += 1
    if special_day: special_days_in_month.append(...)
    if is_dark: dark_week_count += 1

    daily_overview.append({
        "date": day_date.isoformat(),
        "weekday": daily_fortune["weekday"]["name"],
        "score": daily_fortune["fortune"]["overall"],
        "special_day": special_day["name"] if special_day else None,
        "ryouhan_active": is_ryouhan,
        "is_dark_week": is_dark
    })
```

月整體分數依凌犯比例調整：
```python
ryouhan_ratio = ryouhan_count / days_in_month
if ryouhan_ratio > 0.5:
    base_score = max(40, base_score - 15)  # 超過半月凌犯
elif ryouhan_ratio > 0:
    base_score = max(40, base_score - 8)   # 部分凌犯
```

回傳新增 `ryouhan_info` 和 `month_warnings` 欄位。

### P0-3 daily_overview 補充欄位

統一 weekly 和 monthly 的 daily_overview 格式，從 `calculate_daily_fortune()` 回傳中擷取：

```python
daily_overview.append({
    "date": day_date.isoformat(),
    "weekday": daily_fortune["weekday"]["name"],
    "score": daily_fortune["fortune"]["overall"],
    # 新增欄位
    "special_day": special_day_name,      # "甘露日" / "羅刹日" / "金剛峯日" / null
    "ryouhan_active": bool,               # 凌犯期間中
    "is_dark_week": bool                  # 暗黒の一週間
})
```

## 不修改的部分

- 日運計算（已正確）
- 相性計算（已驗證）
- 九曜流年計算（已驗證）
- 前端顯示（新欄位為附加性，不破壞既有結構）

## 測試計畫

1. **年運 monthly_trend**: 查 1977/10/29 的 2026 年 → 12 個月分數不再隨機，各月分數應反映月宿關係差異
2. **月運凌犯**: 查 1988/10/14（尾宿）的凌犯月份 → `ryouhan_info` 欄位出現，分數有調整
3. **weekly daily_overview**: 呼叫週運 API → daily_overview 每日包含 `special_day` / `ryouhan_active` / `is_dark_week`
4. **monthly daily_overview**: 展開月份卡片 → 每日 chip 有特殊日標記
5. **向下相容**: 既有前端不因新增欄位報錯
6. **建構驗證**: `npx vue-tsc --noEmit` 和 `npx vite build` 通過

## Checklist

- [x] P0-1: 年運 monthly_trend 改為月宿關係計算 + 凌犯抽樣
- [x] P0-2: 月運加入凌犯期間偵測與分數調整
- [x] P0-3: 週運/月運 daily_overview 補充 special_day / ryouhan_active / is_dark_week
- [x] 月運回傳新增 ryouhan_info / month_warnings 欄位
- [x] 日運也消除 random.randint（base_score 改中位值、category 移除隨機變異）
- [x] 全檔案零 random.randint
- [x] 5 項測試驗證通過 + vue-tsc + vite build 通過
