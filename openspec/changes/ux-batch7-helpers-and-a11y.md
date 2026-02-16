---
title: 第七批 UX 改善：Helper 提取與 Accessibility
type: refactor
status: in-progress
created: 2026-02-16
---

# 第七批 UX 改善：Helper 提取與 Accessibility

## 變更內容

### 1. 共用 Helper 提取

`getScoreClass()`、`getFortuneLevel()`、`getMansionRelationClass()` 在 5 個檔案中重複定義。
提取到 `utils/fortune-helpers.ts`，各 component import 使用。

### 2. Accessibility 改善

- MatchTab mansion chip 加 `aria-label` 和 `aria-pressed`
- FortuneTab 月運週展開內 daily chip 加 `aria-label`
- KnowledgeTab 手風琴 relation 加 `aria-controls`

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `frontend/src/utils/fortune-helpers.ts` | 新建共用 helper |
| `frontend/src/components/FortuneTab.vue` | import helper + a11y |
| `frontend/src/components/SummaryCard.vue` | import helper |
| `frontend/src/components/MatchTab.vue` | import helper + a11y |
| `frontend/src/components/LuckyDaysTab.vue` | import helper |
| `frontend/src/composables/useSukuyodo.ts` | import helper |

## 測試計畫

1. TypeScript 編譯通過
2. 瀏覽器確認所有分數顏色正確
3. 鍵盤 Tab 導航確認 aria 屬性存在
