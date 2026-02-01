---
title: Sukuyodo 前端遷移
type: feature
status: in-progress
created: 2026-01-31
phase: 1
---

# Sukuyodo 前端遷移

## 變更內容

從 DashAstro 遷移宿曜道前端元件到獨立的 sukuyodo 專案。

## 影響範圍

### 需遷移的檔案

| 來源 (DashAstro) | 目標 (sukuyodo) |
|------------------|-----------------|
| `frontend/src/views/SukuyodoView.vue` | `frontend/src/views/HomeView.vue` |
| `frontend/src/components/sukuyodo/*.vue` | `frontend/src/components/*.vue` |
| `frontend/src/composables/useSukuyodo.ts` | `frontend/src/composables/useSukuyodo.ts` |
| `frontend/src/stores/profile.ts` | `frontend/src/stores/profile.ts` |

### 新建檔案

| 檔案 | 說明 |
|------|------|
| `frontend/vite.config.ts` | Vite 配置 |
| `frontend/src/config/api.ts` | API 配置 |
| `frontend/src/App.vue` | 根元件 |
| `frontend/src/main.ts` | 入口檔案 |
| `frontend/src/styles/main.css` | 全域樣式 |

## UI/UX 規格

### 設計系統

- **色彩**: 沿用 DashAstro 的宿曜道色彩系統
- **間距**: 4px 基數 (4/8/12/16/24/32px)
- **元件**: Shoelace Web Components
- **響應式**: mobile-first

### 頁面結構

```
┌─────────────────────────────────────┐
│ Header: 宿曜道 Logo + 生日查詢      │
├─────────────────────────────────────┤
│ Main Tabs:                          │
│ [運勢] [配對] [吉日] [知識]          │
├─────────────────────────────────────┤
│ Content Area                        │
│ - 運勢: 日/週/月/年                  │
│ - 配對: 配對尋找/相性診斷            │
│ - 吉日: 分類查詢                    │
│ - 知識: 27宿/六種關係/七曜           │
└─────────────────────────────────────┘
```

## 測試計畫

1. 後端 API 測試：`uvicorn main:app --reload --port 8001`
2. 前端開發伺服器：`npm run dev`
3. 本命宿查詢功能
4. 相性診斷功能（含距離類型顯示）
5. 運勢查詢功能
6. 吉日查詢功能

## Checklist

### Phase 1: 後端驗證
- [ ] 建立 venv 並安裝依賴
- [ ] 測試 API 端點
- [ ] 確認資料庫連線

### Phase 2: 前端基礎建設
- [x] 初始化 Vite + Vue 3 + TypeScript
- [x] 設定 Shoelace CDN
- [x] 建立 API 配置
- [x] 遷移全域樣式

### Phase 3: 元件遷移
- [x] 遷移 useSukuyodo composable
- [x] 遷移 profile store
- [x] 遷移 FortuneTab 元件
- [x] 遷移 MatchTab 元件
- [x] 遷移 LuckyDaysTab 元件
- [x] 遷移 KnowledgeTab 元件
- [x] 遷移 SummaryCard 元件

### Phase 4: 整合測試
- [ ] 本命宿查詢
- [ ] 相性診斷
- [ ] 運勢查詢
- [ ] 吉日查詢
