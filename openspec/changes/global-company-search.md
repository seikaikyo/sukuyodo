---
title: 海外公司設立日查詢（美國/日本）
type: feature
status: in-progress
created: 2026-02-28
---

# 海外公司設立日查詢（美國/日本）

## 變更內容

擴充 `CompanySearchService`，新增美國和日本公司的設立日期自動查詢功能。

現有架構：
```
104 搜尋 → GCIS 查設立日 → 宿曜相性計算（僅台灣）
```

目標架構：
```
台灣: 104 搜尋 → GCIS 查設立日 → 相性計算（不變）
日本: 公司名搜尋 → gBizINFO API 查設立日 → 相性計算
美國: 公司名搜尋 → OpenCorporates API 查設立日 → 相性計算
```

## API 資料源

| 國家 | API | 免費 | 有設立日 | 需 API Key |
|------|-----|:----:|:-------:|:----------:|
| 日本 | gBizINFO (經濟産業省) | O | O (`date_of_establishment`) | O (免費申請) |
| 美國 | OpenCorporates | O (200/月) | O (`incorporation_date`) | O |
| 台灣 | GCIS 商工登記 | O | O | X |

## 影響範圍

- `backend/services/company_search.py` — 新增 `_lookup_gbizinfo()`, `_lookup_opencorporates()`，修改 `lookup_founding_date()` 加 country 參數
- `backend/routers/sukuyodo.py` — 新增 `/api/sukuyodo/company-search/global` 端點
- `backend/.env` — 新增 `GBIZINFO_API_TOKEN`, `OPENCORPORATES_API_KEY` (選填)

## 設計決策

1. **不做職缺搜尋整合**：LinkedIn/Indeed/リクナビ 都有反爬蟲機制，只做「公司名 → 設立日 → 相性」
2. **API Key 選填**：沒有 key 時 graceful fallback，回傳錯誤訊息而非假資料
3. **OpenCorporates 免費額度有限 (200/月)**：加 cache 避免重複查詢
4. **gBizINFO token 需申請**：先實作邏輯，token 到手後即可啟用

## 新增端點

```
POST /api/sukuyodo/company-search/global
{
    "company_name": "トヨタ自動車",
    "country": "jp",          # tw / jp / us
    "birth_date": "1977-10-29"
}

回應:
{
    "success": true,
    "data": {
        "name": "トヨタ自動車株式会社",
        "founding_date": "1937-08-28",
        "country": "jp",
        "source": "gbizinfo",
        "compatibility": { ... }  # 完整相性結果
    }
}
```

## 測試計畫

1. 日本: 查詢 トヨタ自動車 / ソニー / 任天堂 的設立日
2. 美國: 查詢 Mercor / Apple / Google 的 incorporation date
3. 台灣: 確認既有 GCIS 查詢不受影響
4. 無 API Key 時的 fallback 行為

## Checklist

- [ ] 新增 `_lookup_gbizinfo()` 方法
- [ ] 新增 `_lookup_opencorporates()` 方法
- [ ] 修改 `lookup_founding_date()` 支援 country 參數
- [ ] 新增 `/company-search/global` API 端點
- [ ] 新增簡易 cache（避免重複查詢同一公司）
- [ ] 測試日本公司查詢
- [ ] 測試美國公司查詢
- [ ] 測試台灣既有功能不受影響
