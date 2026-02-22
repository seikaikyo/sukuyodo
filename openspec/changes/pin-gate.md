---
title: PIN 碼存取門檻
type: feature
status: in-progress
created: 2026-02-22
---

# PIN 碼存取門檻

## 變更內容

部署到 Vercel/Render 後，防止路人隨意使用 API。
加入 PIN 碼輸入畫面，正確輸入後存入 localStorage，後續請求自動帶上。
本地開發不設環境變數則自動跳過。

## 影響範圍

- `frontend/src/components/PinGate.vue` (新增)
- `frontend/src/App.vue` — 加入 PIN 門檻判斷
- `frontend/src/config/api.ts` — 新增 apiFetch 統一帶 PIN header
- `frontend/src/composables/useSukuyodo.ts` — fetch 改用 apiFetch
- `backend/routers/sukuyodo.py` — 新增 PIN 驗證 dependency

## 方案

### 前端
- `VITE_APP_PIN` 未設定 → 跳過 PIN，直接進入
- `VITE_APP_PIN` 已設定 → 顯示 PIN 輸入畫面
- PIN 存 localStorage `sukuyodo_pin`，下次不用重新輸入
- `api.ts` 新增 `apiFetch()`，自動帶 `X-App-Pin` header
- 所有 fetch 呼叫改用 `apiFetch()`

### 後端
- `APP_PIN` 未設定 → 放行所有請求（本地開發）
- `APP_PIN` 已設定 → 檢查 `X-App-Pin` header，不符回 401

## 測試計畫

1. 本地不設環境變數 → 直接進入，API 正常
2. 設 VITE_APP_PIN=1234 → 顯示 PIN 畫面，輸入正確後進入
3. npm run build 通過
