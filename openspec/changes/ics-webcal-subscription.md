---
title: ICS 日曆訂閱功能（webcal://）
type: feature
status: in-progress
created: 2026-03-06
---

# ICS 日曆訂閱功能（webcal://）

## 背景

目前使用者匯出 ICS 後，系統若有更新（如本次原典校正），使用者必須重新匯出再匯入。提供 webcal:// 訂閱 URL，日曆 app 會定期自動抓取最新版本，無需手動操作。

## 設計決策

| 項目 | 決策 |
|------|------|
| 匯出功能 | 保留（離線/一次性使用） |
| 訂閱功能 | 新增（自動更新） |
| URL 隱私 | Token 加密，birth_date 不出現在 URL 中 |
| 訂閱範圍 | 整年 12 個月 |
| 資安標準 | ISO 27001:2022 合規 |

## 技術方案

### Token 設計（無狀態、不可偽造、可逆）

```
payload = "{birth_date}|{year}"
token   = Fernet.encrypt(payload, ICS_TOKEN_SECRET)
URL     = webcal://sukuyodo-backend.onrender.com/api/sukuyodo/calendar/ics/{token}
```

- **Fernet**（cryptography 庫）：AES-128-CBC + HMAC-SHA256，業界標準對稱加密
- **無狀態**：不需要資料庫存 token，伺服器收到請求時解密即可還原 birth_date 和 year
- **不可偽造**：沒有 secret key 就無法產生有效 token
- **有時效**：Fernet 內建 timestamp，可設定 token 過期時間（建議 400 天，涵蓋整年+緩衝）
- **URL safe**：Fernet token 本身是 URL-safe base64

### ISO 27001:2022 合規要點

| 控制措施 | 對應條款 | 實作方式 |
|---------|---------|---------|
| 密鑰管理 | A.8.24 | ICS_TOKEN_SECRET 存環境變數，不進版控 |
| 資料最小化 | A.5.33 | Token 只含 birth_date + year，不含姓名等 PII |
| 傳輸加密 | A.8.24 | HTTPS only（Render 預設） |
| 存取控制 | A.8.3 | Token 有時效，過期需重新取得 |
| 日誌記錄 | A.8.15 | ICS 存取記錄 token hash（不記錄明文） |

### API 設計

#### 1. 產生訂閱 Token

```
POST /api/sukuyodo/calendar/subscribe
Body: { "birth_date": "1977-10-29", "year": 2026 }
Response: {
  "success": true,
  "data": {
    "webcal_url": "webcal://sukuyodo-backend.onrender.com/api/sukuyodo/calendar/ics/{token}",
    "https_url": "https://sukuyodo-backend.onrender.com/api/sukuyodo/calendar/ics/{token}",
    "expires_at": "2027-04-11T00:00:00Z"
  }
}
```

#### 2. 回傳 ICS 內容

```
GET /api/sukuyodo/calendar/ics/{token}
Response: Content-Type: text/calendar; charset=utf-8
          Cache-Control: max-age=3600 (1 小時快取)
```

- 解密 token 取得 birth_date + year
- 呼叫 get_calendar_month() x 12 個月
- 組裝 ICS 內容（移植 ics-generator.ts 邏輯到後端）
- 回傳 text/calendar

### 後端 ICS 產生器

目前 ICS 產生在前端（`ics-generator.ts`）。訂閱需要後端動態產生，需將核心邏輯移植到 Python：

- `buildDayEvent()` -> `_build_ics_day_event()`
- `getDayTip()` -> `_get_ics_day_tip()`
- `generateIcsCalendar()` -> `generate_ics_calendar()`
- RFC 5545 格式處理（fold line、escape text、全天事件）

前端的 `ics-generator.ts` 保留不動（匯出功能繼續用前端版本）。

### 前端 UI

在現有「匯出 ICS」按鈕旁新增「訂閱日曆」按鈕：

- 點擊後呼叫 POST /subscribe 取得 URL
- 顯示 Dialog：
  - webcal:// 連結（點擊直接開啟日曆 app）
  - 複製 URL 按鈕（給手動貼上的使用者）
  - 說明文字：「日曆 app 會每天自動更新，不需要重新匯入」
- Apple 裝置：webcal:// 直接觸發 Calendar.app
- Android/其他：提供 https:// URL 讓使用者手動新增

## 影響範圍

| 檔案 | 修改內容 |
|------|---------|
| `backend/main.py` | 新增 2 個 API endpoint |
| `backend/services/sukuyodo.py` | 新增 ICS 產生器（Python 版） |
| `backend/services/ics_token.py` | 新增 Token 加解密模組 |
| `frontend/src/components/FortuneCalendar.vue` | 新增訂閱按鈕 + Dialog |
| `frontend/src/composables/useSukuyodo.ts` | 新增 subscribe API 呼叫 |
| Render 環境變數 | 新增 ICS_TOKEN_SECRET |

## 測試計畫

1. Token 加解密：正確還原 birth_date + year
2. Token 過期：超過 400 天的 token 回傳 410 Gone
3. Token 偽造：隨機字串回傳 403 Forbidden
4. ICS 內容：Apple Calendar / Google Calendar 可正確匯入
5. ICS 快取：Cache-Control header 正確
6. webcal:// URL：iOS Safari 點擊可觸發 Calendar.app
7. HTTPS：HTTP 請求 redirect 到 HTTPS
8. 日誌：存取記錄只含 token hash，不含明文

## Checklist

- [ ] 新增 ICS_TOKEN_SECRET 環境變數（Render）
- [ ] 實作 ics_token.py（Fernet 加解密）
- [ ] 實作後端 ICS 產生器（移植 ics-generator.ts）
- [ ] 實作 POST /subscribe endpoint
- [ ] 實作 GET /ics/{token} endpoint
- [ ] 前端訂閱按鈕 + Dialog
- [ ] Apple Calendar 實機測試
- [ ] Google Calendar 實機測試
- [ ] Token 過期/偽造測試
- [ ] ISO 27001 合規檢查（密鑰管理、日誌、傳輸加密）
