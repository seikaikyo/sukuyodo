---
title: 公司速查自動搜尋
type: feature
status: completed
created: 2026-02-21
---

# 公司速查自動搜尋

## 變更內容

在公司速查頁面新增「自動搜尋」功能。後端新增 API 端點，接受搜尋關鍵字和地區，自動爬取 104.com.tw 職缺列表、查詢公司設立日期、計算宿曜相性，回傳排序後的推薦公司清單。前端加搜尋按鈕呼叫此 API。

## 影響範圍

- `backend/requirements.txt` — 新增 httpx, beautifulsoup4
- `backend/services/company_search.py` — 新檔，爬蟲 + 整合邏輯
- `backend/routers/sukuyodo.py` — 新增 `/company-search` 端點
- `frontend/src/composables/useSukuyodo.ts` — 新增搜尋狀態/函式
- `frontend/src/components/MatchTab.vue` — 新增搜尋 UI + jobUrl 顯示
- `frontend/src/views/HomeView.vue` — 綁定新 props/events
- `frontend/src/stores/profile.ts` — Company 介面新增 jobUrl，匯入改為以 JSON 為準
- `frontend/public/companies.json` — 推薦公司清單（13 間）

## 技術備註

- 104 JSON API: `https://www.104.com.tw/jobs/search/api/jobs`
- 設立日期來源（主要）: GCIS 經濟部商工登記開放資料 API（免 Key、民國日期自動轉西曆）
- 設立日期來源（備援）: findcompany.com.tw
- GCIS API: `https://data.gcis.nat.gov.tw/od/data/api/6BBA2268-1367-4B42-9CCA-BC17499EBE8C`
- 民國日期轉換: 7 碼 `YYYMMDD`，西元年 = 民國年 + 1911
- API 回應時間約 30-60 秒（需爬取外部網站）
- 中文關鍵字 Referer 需 URL encode（urllib.parse.quote）

## 測試結果

1. curl 測試 `/company-search` — 通過，回傳 49 間公司
2. 搜尋 "MES" 台南 — 成功找到公司並算出相性
3. GCIS 查詢 — 4 間測試公司全部正確（友勁/緯穎/三隆/家登）
4. GCIS 查不到時 — 自動 fallback 到 findcompany
5. 中文關鍵字搜尋（智慧製造/專案主管等）— 通過
6. 匯入推薦清單 — 以 companies.json 為準，清空再匯入
7. TypeScript 檢查 — 通過
8. Vite build — 通過

## Checklist

- [x] 後端 httpx + bs4 安裝
- [x] CompanySearchService 實作
- [x] /company-search 端點
- [x] 前端搜尋 UI
- [x] 前端結果顯示 + 收藏
- [x] jobUrl 欄位（104 職缺連結）
- [x] 匯入邏輯改為以 JSON 為準
- [x] 中文關鍵字 Referer 編碼修正
- [x] GCIS 官方 API 整合（主要查詢來源）
- [x] findcompany 降為備援
- [x] companies.json 篩選（過濾低薪/派遣/純開發）
- [x] 端對端測試
