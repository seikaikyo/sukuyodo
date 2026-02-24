---
title: 公司卡片豐富化 + 吉凶日曆
type: feature
status: in-progress
created: 2026-02-23
---

# 公司卡片豐富化 + 吉凶日曆

## 變更內容

公司速查的卡片目前資訊太少，只有公司名、宿名、相性和分數。要把實用資訊放上去：
1. 職缺名稱/地點（memo）直接顯示在卡片摘要
2. 104 職缺外部連結 icon
3. 投遞/面試吉日（事業分 >= 80 的近期好日子）
4. 應避開的凶日（安壊/暗黒/凌犯日）
5. 暗黒の一週間警告

## 影響範圍

| 檔案 | 變更 |
|------|------|
| `backend/routers/sukuyodo.py` | 新增 lucky-dates endpoint |
| `backend/services/company_search.py` | 新增 calculate_lucky_dates() |
| `frontend/src/composables/useSukuyodo.ts` | 新增 LuckyDate interface + fetchLuckyDates |
| `frontend/src/views/HomeView.vue` | 串接 lucky dates 呼叫 |
| `frontend/src/components/MatchTab.vue` | 卡片 memo + 吉凶面板 + CSS |

## UI/UX 規格

- memo: 12px, #888, 單行省略
- 104 連結: pi-external-link icon, 點擊不展開卡片
- 吉日 chip: 暖金背景 #f0e6d2, 圓角 4px
- 凶日 chip: 淡紅背景 #f5e0e0, 圓角 4px
- 暗黒警告: 深底 #333 + 金字 #ffd700
- 間距: 4px 倍數 (8px gap between chips, 12px panel margin)

## 測試計畫

1. 卡片摘要顯示 memo + 104 icon
2. 點 icon 開新分頁（卡片不展開）
3. 吉凶面板各顯示 5 個日期 chip
4. hover chip 看完整原因
5. 暗黒の一週間警告條
6. 求職者切換，吉凶日期跟著切換
7. Vite build 通過

## Checklist

- [ ] 後端 lucky-dates endpoint
- [ ] 前端 interface + API
- [ ] HomeView 串接
- [ ] MatchTab 卡片 memo + icon
- [ ] MatchTab 吉凶面板
- [ ] CSS 樣式
- [ ] 測試通過
