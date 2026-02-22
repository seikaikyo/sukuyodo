---
title: 修正 83 個 TypeScript 編譯錯誤
type: fix
status: completed
created: 2026-02-22
---

# 修正 83 個 TypeScript 編譯錯誤

## 變更內容
後端 API 陸續新增欄位（reading、siddham、source 等），前端型別定義未跟上，導致 `npm run build` 產生 83 個 TS 錯誤，Vercel 部署會失敗。

主要修正：
- 補齊 useSukuyodo.ts 中 37 個缺失欄位的型別定義
- 移除未使用的變數/import（9 個）
- 補 null/undefined guard（22+）
- 修正型別不符（8 個）

## 影響範圍
- `frontend/src/composables/useSukuyodo.ts`
- `frontend/src/utils/report-generator.ts`
- `frontend/src/utils/ics-generator.ts`
- `frontend/src/views/HomeView.vue`
- `frontend/src/components/MansionWheel.vue`
- `frontend/src/components/MatchTab.vue`
- `frontend/src/components/FortuneCalendar.vue`
- `frontend/src/components/SummaryCard.vue`（間接，靠型別補齊解決）
- `frontend/src/components/KnowledgeTab.vue`（間接，靠型別補齊解決）
- `frontend/src/components/FortuneTab.vue`（間接，靠型別補齊解決）

## 測試計畫
1. `npm run build` 通過，0 errors
2. 不改任何運行邏輯，純型別修正

## Checklist
- [x] useSukuyodo.ts 型別定義補齊
- [x] report-generator.ts 未使用變數 + null guard
- [x] HomeView.vue 未使用 import + tab 型別
- [x] ics-generator.ts 未使用參數 + undefined check
- [x] MansionWheel.vue 未使用 import/變數 + undefined check
- [x] MatchTab.vue null vs undefined
- [x] FortuneCalendar.vue undefined check
- [x] npm run build 通過
