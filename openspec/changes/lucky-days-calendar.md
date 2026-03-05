---
title: 吉日月曆化 + 雙人吉日白話建議
type: feature
status: completed
created: 2026-03-04
---

# 吉日月曆化 + 雙人吉日白話建議

## 變更內容

1. **個人吉日月曆化**：列表改為月曆格子，以日期為單位一覽所有吉日
2. **雙人吉日月曆化**：同上，action 列表改為月曆
3. **雙人白話建議**：每個吉日附帶 advice（summary/宜/忌），依關係品質分檔

## 影響範圍

- `backend/services/sukuyodo.py` — 新增 `get_lucky_days_calendar()`, `get_pair_lucky_days_calendar()`, `PAIR_ADVICE_TEMPLATES`
- `backend/routers/sukuyodo.py` — 新增 2 個月曆路由
- `frontend/src/components/LuckyCalendar.vue` — **新增** 吉日月曆元件
- `frontend/src/components/LuckyDaysTab.vue` — 列表改月曆
- `frontend/src/composables/useSukuyodo.ts` — 新增型別 + fetch 函式
- `frontend/src/views/HomeView.vue` — 傳遞新 props

## 測試計畫

1. API 測試確認月曆端點回傳整月日期分組正確
2. 雙人白話建議確認 advice 欄位包含 summary/do/avoid
3. `vue-tsc --noEmit` 無錯誤
4. `vite build` 建構成功
