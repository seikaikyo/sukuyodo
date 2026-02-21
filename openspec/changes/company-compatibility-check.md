---
title: 公司相性速查
type: feature
status: completed
created: 2026-02-21
---

# 公司相性速查

## 變更內容

在相性頁面新增「公司速查」子分頁，輸入公司名稱與設立日期，即可查出與使用者的宿曜相性關係、適配度評分，以及針對職場情境的建議。

核心邏輯完全複用現有 `calculate_compatibility()` ，僅需：
1. 前端新增子分頁 UI
2. 後端新增公司情境的解讀文字（career/business context）
3. 本地儲存已查詢的公司清單

## 影響範圍

- `frontend/src/components/MatchTab.vue` — 新增第 4 個子分頁 "company"
- `frontend/src/composables/useSukuyodo.ts` — 新增 `calculateCompanyCompatibility()` 函式
- `frontend/src/stores/profile.ts` — 新增 companies 陣列與 CRUD
- `backend/routers/sukuyodo.py` — 可選：新增 `/company-compatibility` 端點（或直接複用 `/compatibility`）

## 設計規格

### UI 配置
- 新子分頁標籤：「公司速查」，icon: `pi pi-building`
- 輸入區：公司名稱（InputText）+ 設立日期（DatePicker）+ 查詢按鈕
- 結果區：相性分數、關係類型、距離、職場建議
- 已儲存公司列表（類似 Partners 分頁）

### 職場情境建議
- 複用 relation.career 欄位
- 額外提供「是否適合投履歷」的簡要判斷（基於關係類型 + 方向）

## 測試計畫
1. 輸入已知公司設立日，確認算出正確本命宿
2. 確認相性結果與手動用「雙人相性」查出的結果一致
3. 儲存/刪除公司功能正常
4. RWD 在 mobile/tablet/desktop 正常顯示

## Checklist
- [x] 前端子分頁 UI
- [x] 複用 compatibility API
- [x] 公司清單本地儲存
- [x] 職場情境建議文字（投履歷判定三級制）
- [x] TypeScript 型別檢查通過
- [x] Vite build 通過
