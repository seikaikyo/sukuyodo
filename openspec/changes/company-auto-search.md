---
title: 公司速查自動搜尋
type: feature
status: completed
created: 2026-02-21
---

# 公司速查自動搜尋

## 變更內容

在公司速查頁面新增「自動搜尋」功能。後端新增 API 端點，接受搜尋關鍵字和地區，自動爬取 104.com.tw 職缺列表、從 findcompany.com.tw 查詢公司設立日期、計算宿曜相性，回傳排序後的推薦公司清單。前端加搜尋按鈕呼叫此 API。

## 影響範圍

- `backend/requirements.txt` — 新增 httpx, beautifulsoup4
- `backend/services/company_search.py` — 新檔，爬蟲 + 整合邏輯
- `backend/routers/sukuyodo.py` — 新增 `/company-search` 端點
- `frontend/src/composables/useSukuyodo.ts` — 新增搜尋狀態/函式
- `frontend/src/components/MatchTab.vue` — 新增搜尋 UI
- `frontend/src/views/HomeView.vue` — 綁定新 props/events

## 技術備註

- 104 JSON API: `https://www.104.com.tw/jobs/search/api/jobs`（非原先預設的 list endpoint）
- 設立日期來源: findcompany.com.tw（twincn 已無法正常查詢）
- API 回應時間約 30-60 秒（需爬取外部網站）

## 測試結果

1. curl 測試 `/company-search` — 通過，回傳 39 間公司
2. 搜尋 "MES" 台南 — 成功找到公司並算出相性
3. findcompany 查詢失敗時 — 優雅跳過該公司
4. TypeScript 檢查 — 通過
5. Vite build — 通過
6. Python import — 通過

## Checklist

- [x] 後端 httpx + bs4 安裝
- [x] CompanySearchService 實作
- [x] /company-search 端點
- [x] 前端搜尋 UI
- [x] 前端結果顯示 + 收藏
- [x] 端對端測試
