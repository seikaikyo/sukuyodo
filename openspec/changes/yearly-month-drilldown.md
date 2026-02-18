---
title: 本年月份卡片展開週/日資料
type: feature
status: in-progress
created: 2026-02-18
---

# 本年月份卡片展開週/日資料

## 變更內容

「本年」頁籤的 12 個月份卡片改為可點擊展開，顯示該月的週次概覽與每日分數。點擊日期可跳轉到「今日」頁籤查看詳情。

互動路徑：本年 → 點月份 → 週次概覽 → 點日期 → 今日頁籤

## 影響範圍

- `frontend/src/components/FortuneTab.vue` — 月份卡片加展開邏輯、週/日模板
- `frontend/src/composables/useSukuyodo.ts` — 新增 fetchMonthlyFortuneForMonth 函式

## UI/UX 規格

- 點擊月份卡片展開，再點收合（accordion 模式，同時只展開一個）
- 展開內容沿用「本月」頁籤內的週次展開樣式（weekly-item + week-detail）
- 當月卡片預設不展開，需手動點擊
- 展開時顯示載入 spinner，資料到後顯示內容
- 每日 chip 可點擊，觸發 selectDay 跳轉今日頁籤

## 測試計畫

1. 點擊任一月份卡片 → 展開顯示週次列表
2. 點擊週次 → 展開顯示每日分數 chip
3. 點擊日期 chip → 跳轉到今日頁籤顯示該日運勢
4. 同時只有一個月份展開
5. vue-tsc --noEmit 和 vite build 通過

## Checklist

- [ ] useSukuyodo 新增 fetchMonthlyFortuneForMonth
- [ ] 月份卡片加展開/收合互動
- [ ] 展開區顯示週次概覽 + 每日 chip
- [ ] 點日期 chip 觸發 selectDay
- [ ] 建構驗證通過
