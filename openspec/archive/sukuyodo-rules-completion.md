---
title: 宿曜經規則補完與 UI 改善
type: feature
status: completed
created: 2026-02-16
---

# 宿曜經規則補完與 UI 改善

## 變更內容

1. 新增甘露日/金剛峯日/羅刹日判定（宿曜經卷五核心規則）
2. 年運勢改用九曜流年法取代天干地支
3. 修正 `_is_generating` 缺少日/月特殊元素
4. KnowledgeTab 六種關係改為直接展開（減少點擊）

## 影響範圍

- `backend/services/sukuyodo.py` — 新增甘露日常數、修改每日運勢回傳、修正 _is_generating、改寫年運勢計算
- `frontend/src/components/FortuneTab.vue` — 每日運勢新增甘露日/羅刹日顯示、年運勢改用九曜
- `frontend/src/components/KnowledgeTab.vue` — 六種關係移除 accordion
- `frontend/src/composables/useSukuyodo.ts` — DailyFortune 新增 special_day 欄位、YearlyFortune 調整九曜欄位

## 測試計畫

1. curl 測試 daily API 確認甘露日/金剛峯日/羅刹日正確回傳
2. curl 測試 yearly API 確認九曜流年正確
3. 前端確認日運勢特殊日顯示、年運勢九曜顯示、知識 tab 無 accordion
