---
title: GCIS 公司查詢整合
type: feature
status: completed
created: 2026-02-23
---

# GCIS 公司查詢整合

## 變更內容

將經濟部商工登記 (GCIS) API 直接串進前端手動查詢流程。用戶輸入公司名稱後自動搜尋 GCIS，選擇結果即自動帶入設立日期，不需再手動查詢經濟部網站。

後端已有 GCIS 整合（`company_search.py` 的 `_lookup_gcis()`），本次新增獨立搜尋端點和前端 UI。

## 影響範圍

- `backend/services/company_search.py` - 新增 `search_gcis()` 方法
- `backend/routers/sukuyodo.py` - 新增 `POST /gcis/search` 端點
- `frontend/src/composables/useSukuyodo.ts` - 新增 GCIS 搜尋 interface + function
- `frontend/src/views/HomeView.vue` - 傳遞 GCIS props/events
- `frontend/src/components/MatchTab.vue` - GCIS 下拉搜尋 UI

## 測試計畫

1. 輸入「研華」→ 下拉顯示研華股份有限公司
2. 選擇後設立日期自動填入 1981-09-07
3. 查詢相性正常（業胎 80 分）
4. GCIS 不可用時仍可手動輸入設立日期
5. Vite build 通過

## Checklist

- [x] 後端 search_gcis() 方法
- [x] POST /gcis/search 端點
- [x] 前端 searchGcis() + interface
- [x] HomeView props 串接
- [x] MatchTab GCIS 下拉 UI
- [x] 驗證測試
