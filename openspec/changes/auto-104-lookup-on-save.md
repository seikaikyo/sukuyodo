---
title: 收藏公司時自動查詢 104 職缺連結
type: feature
status: in-progress
created: 2026-02-26
---

# 收藏公司時自動查詢 104 職缺連結

## 變更內容

使用者透過 GCIS 查詢公司並確認相性後，點擊「收藏此公司」時，系統自動用公司名稱查詢 104 人力銀行的公司頁面連結，並存入 jobUrl 欄位。

目前流程：
```
GCIS 查公司 → 算相性 → 點「收藏」→ jobUrl 空白，需手動補
```

改善後：
```
GCIS 查公司 → 算相性 → 點「收藏」→ 自動查 104 → jobUrl 自動填入
```

## 實作方案

### 後端：新增 104 公司頁面查詢端點

在 `backend/routers/sukuyodo.py` 新增端點：

```
POST /api/sukuyodo/104/company-url
Request: { "company_name": "研華股份有限公司" }
Response: { "success": true, "data": { "job_url": "https://www.104.com.tw/company/2d9ntmw" } }
```

利用既有的 `search_104` 方法，用公司名稱搜尋，取第一筆符合的公司頁面 URL。
104 JSON API 回傳的 `link.cust` 欄位即為公司頁面連結。

### 前端：收藏時自動查詢

在 `HomeView.vue` 的 `handleSaveCompany` 中，若傳入的 `jobUrl` 為空，先呼叫後端查詢 104 連結，再存入 profile。

## 影響範圍

- `backend/routers/sukuyodo.py` - 新增 API 端點
- `backend/services/company_search.py` - 新增 `lookup_104_company_url` 方法
- `frontend/src/views/HomeView.vue` - `handleSaveCompany` 加入自動查詢邏輯
- `frontend/src/composables/useSukuyodo.ts` - 新增 `lookup104CompanyUrl` 函式

## 測試計畫

1. 手動輸入「研華」查 GCIS → 相性查詢 → 收藏 → 確認 jobUrl 自動填入
2. 輸入查不到的公司名稱 → 收藏 → jobUrl 維持空白，不影響收藏流程
3. 已有 jobUrl 的收藏（如自動搜尋 104 職缺的結果）→ 不重複查詢

## Checklist

- [ ] 後端新增 `/104/company-url` 端點
- [ ] `company_search.py` 新增 `lookup_104_company_url` 方法
- [ ] 前端 `handleSaveCompany` 加入自動查詢
- [ ] 測試：有結果 / 無結果 / 已有 jobUrl 三種情境
