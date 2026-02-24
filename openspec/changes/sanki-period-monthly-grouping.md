---
title: 月運勢子區間改用三期サイクル分組（取代西曆 7 天週）
type: refactor
status: in-progress
created: 2026-02-24
---

# 月運勢子區間改用三期サイクル分組

## 變更內容

將月運勢的「每週概覽」從西曆固定 7 天分組，改為依據宿曜經原典的三期サイクル（一九/二九/三九）分組。

現狀：每月固定切 7 天為一週（1~7, 8~14, 15~21, 22~28, 29~31），導致第 5 週只有 1~3 天。
改後：按三期サイクル（每期 9 天，27 日循環）的實際日期分組，每月 3~4 個區段。

## 影響範圍

- `backend/services/sukuyodo.py` — calculate_monthly_fortune() 週分組邏輯
- `frontend/src/composables/useSukuyodo.ts` — MonthlyFortune 型別定義
- `frontend/src/components/FortuneTab.vue` — 月運/年運的週間概覽渲染

## 測試計畫

1. API 測試：確認 2026/2（28天）和 2026/3（31天）的 periods 分組正確
2. 前端測試：月運勢和年運勢月份鑽取的三期顯示正確
3. 驗證：三期名稱、暗黒の一週間標記、日數與 daily API 的 sanki 資料一致

## Checklist

- [ ] 後端：all_daily 加入 sanki 欄位
- [ ] 後端：weekly 分組改為三期分組
- [ ] 前端：型別定義更新
- [ ] 前端：FortuneTab 月運渲染改用三期
- [ ] 前端：FortuneTab 年運月份鑽取改用三期
- [ ] API 測試通過
