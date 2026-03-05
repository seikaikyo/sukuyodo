---
title: 移除 RC 功能 + 強化相性分析白話描述
type: refactor
status: completed
created: 2026-03-04
---

# 移除 RC 功能 + 強化相性分析白話描述

## 變更內容

1. **移除 Reference Check (RC)**：RC 風險估算功能不符使用者需求，全面移除
2. **強化 strategic summary reason 文字**：「因果牽連深」等簡略描述改為白話詳細說明
3. **強化 recommendation 投遞建議**：加入方向分析和相性解讀的白話文字

## 影響範圍

- `backend/services/company_search.py` — 移除 _estimate_ref_check, 修改 _build_recommendation, 改善 _build_strategic_summary
- `frontend/src/composables/useSukuyodo.ts` — 移除 CompanyRefCheck interface
- `frontend/src/components/MatchTab.vue` — 移除 RC UI 和 CSS

## 測試計畫

1. API 測試確認 ref_check 欄位已移除
2. strategic_summary reason 文字驗證
3. 前端建構無錯誤
