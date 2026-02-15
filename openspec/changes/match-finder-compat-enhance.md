---
title: 配對頁面優化 - Finder 簡化 + 相性角色別建議
type: feature
status: completed
created: 2026-02-15
---

# 配對頁面優化

## 變更內容

### 1. Finder 詳細說明直接展開
移除「查看詳細說明」折疊按鈕，detailed 直接顯示在 description 下方。

### 2. 移除宿位農曆日期對照
點擊宿後不再顯示農曆→西曆日期對照區段（使用者可用相性診斷查詢）。
同步清除 MatchTab.vue 的殘留 CSS 和 useSukuyodo.ts 的 expandedLunarDates/toggleLunarDate。

### 3. 相性診斷加入角色別建議
在相性結果中加入不同身份的相處說明：
- 同事/工作夥伴
- 朋友
- 戀人/配偶
- 家人

後端新增 `ROLE_DESCRIPTIONS` 字典（6 關係類型 x 4 角色 = 24 條，每條 120-180 字）。
前端相性診斷和我的配對展開卡片皆顯示角色別指南。

## 影響範圍
- `frontend/src/components/MatchTab.vue` - Finder 簡化 + 農曆移除 + 角色別顯示
- `frontend/src/composables/useSukuyodo.ts` - Relation interface 加 roles、清除 lunar 殘留
- `frontend/src/views/HomeView.vue` - 清除 lunar props/events
- `backend/services/sukuyodo.py` - ROLE_DESCRIPTIONS + calculate_compatibility 回傳 roles

## 測試計畫
1. Finder 頁面確認 detailed 直接顯示、無農曆日期區段
2. 相性診斷確認角色別建議正確顯示（4 角色卡片）
3. 我的配對展開後也顯示角色別建議

## Checklist
- [x] Finder detailed 直接顯示
- [x] 移除農曆日期對照（template + CSS + composable）
- [x] 後端 ROLE_DESCRIPTIONS（6 類型 x 4 角色）
- [x] calculate_compatibility 回傳 roles
- [x] Relation interface 加 roles
- [x] 相性診斷頁面顯示角色別卡片
- [x] 我的配對展開卡片顯示角色別卡片
- [x] TypeScript 型別檢查通過
- [x] Python import 測試通過
