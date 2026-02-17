---
title: 專有名詞連結至知識頁面
type: feature
status: completed
created: 2026-02-17
---

# 專有名詞連結至知識頁面

## 變更內容
將前端各處顯示的宿曜道專有名詞（七科分宿、五行、六種關係、特殊日等）從純文字改為可點擊連結，點擊後導航至對應的知識 tab 說明頁面。

## 影響範圍（18 處，5 個元件）

| 元件 | 術語 | 目標 tab |
|------|------|---------|
| `KnowledgeTab.vue` | nature_type badge (安住宿等) | `nature-types` |
| `KnowledgeTab.vue` | element badge x2 (本命宿/二十七宿) | `elements` |
| `SummaryCard.vue` | element badge | `elements` |
| `SummaryCard.vue` | mansion_relation.name | `relations` |
| `MatchTab.vue` | element badge/tag x4 | `elements` |
| `MatchTab.vue` | element_mini_tag (相生/相剋) | `elements` |
| `MatchTab.vue` | relation.name x2 | `relations` |
| `MatchTab.vue` | distance_type_name x2 | `relations` |
| `FortuneTab.vue` | hint-relation | `relations` |
| `FortuneTab.vue` | special_day name/level | `special-days` |
| `FortuneTab.vue` | ryouhan label | `ryouhan` |
| `FortuneTab.vue` | rokugai label | `relations` |
| `FortuneTab.vue` | sanki period/day_type/dark_week | `sanki` |
| `FortuneTab.vue` | kuyou star name/level | `kuyou` |
| `LuckyDaysTab.vue` | special_day_type_badge | `special-days` |
| `LuckyDaysTab.vue` | ryouhan-tag | `ryouhan` |

## 導航機制
- `useSukuyodo.ts` 新增 `goToKnowledge(tab)` 函式，同時切換 `activeMainTab='knowledge'` + `activeKnowledgeTab=tab`
- 各元件透過 composable 或 emit 呼叫此函式
- 可點擊的術語加上 `term-link` CSS class（cursor:pointer + 底線提示）

## 測試計畫
1. 點擊各處專有名詞，確認正確跳轉到對應知識 tab
2. 確認觸控裝置上 touch target 足夠大
3. 確認不影響既有的 badge 樣式

## Checklist
- [ ] useSukuyodo.ts 新增 goToKnowledge 導航函式
- [ ] KnowledgeTab.vue 內部術語連結 (3處)
- [ ] SummaryCard.vue 術語連結 (2處)
- [ ] FortuneTab.vue 術語連結 (6處)
- [ ] MatchTab.vue 術語連結 (9處)
- [ ] LuckyDaysTab.vue 術語連結 (2處)
- [ ] term-link 共用樣式
