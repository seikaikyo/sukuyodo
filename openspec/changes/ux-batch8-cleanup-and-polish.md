---
title: UX Batch 8 - 死代碼移除、展開滾動、視覺對比
type: refactor
status: in-progress
created: 2026-02-16
---

# UX Batch 8 - 死代碼移除、展開滾動、視覺對比

## 變更內容

1. **移除 `fortuneLoading` 死代碼** — composable 中 5 個 fetch 函式都在設定 `fortuneLoading.value`，但沒有任何元件讀取這個 ref。FortuneTab 用 `v-if="dailyFortune"` / `v-else` 判斷 spinner。移除無用的 loading 控制。

2. **Partner card 展開自動滾動** — MatchTab 的「我的配對」展開詳情後，在 mobile 上內容常超出可見區域。加 `scrollIntoView` 讓展開的卡片可見。

3. **Kuyou 表格行背景色對比度** — KnowledgeTab 的九曜表格 `rgba(..., 0.08)` 太淡，肉眼幾乎看不出差異。提高到 `0.15`。

## 影響範圍
- `frontend/src/composables/useSukuyodo.ts` — 移除 fortuneLoading 設定
- `frontend/src/components/MatchTab.vue` — scrollIntoView
- `frontend/src/components/KnowledgeTab.vue` — 背景色 alpha

## 測試計畫
1. tsc --noEmit 無錯誤
2. FortuneTab spinner 行為不變
3. MatchTab 展開 partner 會滾動到內容
4. KnowledgeTab 九曜表格行背景色可辨識
