---
title: 趨吉避凶策略分析功能
type: feature
status: in-progress
created: 2026-02-20
---

# 趨吉避凶策略分析功能

## 變更內容

在年運勢和月運勢中加入「趨吉避凶」策略分析，將月趨勢資料從單純的分數列表提升為可行動的建議。

### 年運勢新增欄位：`strategy`

```json
{
  "strategy": {
    "best_months": [
      {
        "month": 9,
        "score": 83,
        "reason": "雙榮親高分，無凌犯，適合重要決策"
      }
    ],
    "caution_months": [
      {
        "month": 7,
        "score": 43,
        "reason": "凌犯57%+安壊，避免大型投資與簽約"
      }
    ],
    "safe_havens": [
      {
        "months": [5, 6],
        "type": "eishin_cluster",
        "description": "連續榮親月，年度最佳行動窗口"
      }
    ],
    "ryouhan_warning": {
      "affected_months": [6, 7, 12],
      "total_ratio": 0.14,
      "advice": "凌犯主要集中在6-7月，重要事項提前至上半年或延後至秋季"
    },
    "yearly_rhythm": "前高後穩型：上半年積極進取，下半年鞏固成果"
  }
}
```

### 分析邏輯

1. **避風港識別**（safe_havens）
   - 連續 2+ 個月分數 >= 65 → 標記為避風港
   - 榮親連續月特別標記為 `eishin_cluster`
   - 業胎連續月標記為 `gyotai_cluster`

2. **最佳月份**（best_months）
   - 取月趨勢中分數 top 3 且無凌犯的月份
   - 附帶宿關係和建議用途

3. **警戒月份**（caution_months）
   - 凌犯 >= 50% 的月份
   - 安壊關係的月份
   - 暗黒の一週間佔比高的月份

4. **凌犯預警**（ryouhan_warning）
   - 彙整全年凌犯月份和總比率
   - 基於凌犯分布給出避讓策略

5. **年度節奏**（yearly_rhythm）
   - 分析上半年/下半年的分數趨勢
   - 歸類為：前高後低/前低後高/前高後穩/V型反轉/平穩 等模式

### 月運勢新增欄位：`weekly_strategy`

```json
{
  "weekly_strategy": {
    "best_days": [
      { "date": "2026-03-15", "score": 95, "reason": "榮親+金剛峯日" }
    ],
    "avoid_days": [
      { "date": "2026-03-05", "score": 35, "reason": "安壊+暗黒の一週間" }
    ],
    "action_windows": [
      { "start": "2026-03-13", "end": "2026-03-17", "type": "高分連續段" }
    ]
  }
}
```

## 影響範圍

- `backend/services/sukuyodo.py` — 新增策略分析函數（~150行）
- `backend/routers/sukuyodo.py` — 年/月運勢 response 加入新欄位
- `frontend/src/components/FortuneTab.vue` — 顯示策略分析區塊（如有）

## 設計原則

- 純後端計算，不引入新依賴
- 附加欄位，不改動既有資料結構（向下相容）
- 策略文字使用三語（zh/ja/classic）
- 分析邏輯基於既有的月趨勢資料，不增加 API 呼叫

## 測試計畫

1. 用 1977/10/29 驗證 2026 年策略分析
   - best_months 應包含 2月(88)、9月(83)
   - caution_months 應包含 7月(43, 凌犯57%)
   - safe_havens 應識別出榮親連續月
2. 用 1991/01/27 驗證 2026 年
   - best_months 應包含 4月(83)、9月(83)
3. 大凶年（2027 火曜星）的策略應正確識別榮親避風港
4. API 向下相容：既有欄位不變

## Checklist

- [ ] 設計策略分析資料結構
- [ ] 實作年運勢 `_generate_yearly_strategy()` 函數
- [ ] 實作月運勢 `_generate_monthly_strategy()` 函數
- [ ] 年度節奏分類邏輯
- [ ] 避風港識別演算法
- [ ] API 回傳加入新欄位
- [ ] 三語策略描述
- [ ] 測試驗證
