---
title: 公司批次分析增強 — 梯隊排名 + 流年 + Reference Check
type: feature
status: in-progress
created: 2026-02-22
---

# 公司批次分析增強

## 變更內容
新增公司批次分析 API 和前端梯隊分組 UI，整合相性分數、公司九曜流年、Reference Check 風險估算和投遞建議。

## 影響範圍
- `backend/services/company_search.py` — 新增 batch_analyze + 梯隊 + ref check 方法
- `backend/routers/sukuyodo.py` — 新增 POST /company-batch-analysis 端點
- `frontend/src/composables/useSukuyodo.ts` — 新增型別和 API 方法
- `frontend/src/components/MatchTab.vue` — 已收藏列表改為梯隊分組
- `frontend/src/views/HomeView.vue` — 傳入新 props

## 測試計畫
1. curl 測試批次 API 回傳結構正確
2. npm run build 通過
3. UI 驗證梯隊分組、流年 badge、RC 風險顯示

## Checklist
- [ ] 後端 batch_analyze 方法
- [ ] 後端 API 端點
- [ ] 前端型別定義
- [ ] 前端 UI 梯隊分組
- [ ] HomeView 接線
- [ ] 驗證
