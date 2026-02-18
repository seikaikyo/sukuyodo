---
title: 本年月度運勢 + 查詢/檔案分離
type: feature
status: completed
created: 2026-02-18
---

# 本年月度運勢 + 查詢/檔案分離

## 現況問題

1. **流年缺月度細節**: API 回傳 `monthly_trend`（12 個月分數+提示），但前端完全沒顯示。用戶看不出「什麼時候會發生什麼事」
2. **查詢和收藏混在一起**: 查詢面板內嵌收藏管理，操作混亂

## 變更內容

### A. 流年頁籤加入「本年」月度展示

現有頁籤: 今日 | 本週 | 本月 | 流年

改為: 今日 | 本週 | 本月 | **本年** | 流年

「本年」頁籤內容:
- 當年九曜星摘要（沿用現有 current-year-summary）
- 12 個月時間軸卡片，每月顯示:
  - 月份
  - 分數（色彩標示吉凶）
  - 月度提示 tip（API 已有 monthly_trend.tip）
- 月度折線圖（12 個月趨勢）

資料來源: `yearlyFortune.monthly_trend[]` — API 已回傳，無需後端修改

### B. 查詢面板移除收藏管理

查詢面板只保留:
- 日期輸入
- 快速選擇 chip（我 + 收藏對象）
- 查詢/取消按鈕

收藏管理移到 header 區域的獨立入口（齒輪或人像 icon），開啟獨立面板。

## 影響範圍

- `frontend/src/components/FortuneTab.vue` — 新增「本年」頁籤 + 月度時間軸
- `frontend/src/views/HomeView.vue` — 查詢面板移除收藏管理、header 新增檔案入口
- `frontend/src/composables/useSukuyodo.ts` — 新增 activeFortuneTab 'yearly' 值

## 測試計畫

1. 切換到「本年」頁籤 → 顯示 12 個月時間軸
2. 每月卡片顯示分數和提示文字
3. 查詢面板只有日期輸入和快速選擇
4. 檔案管理入口開啟獨立面板，CRUD 正常

## Checklist

- [x] FortuneTab 新增「本年」頁籤
- [x] 月度時間軸卡片（12 個月）
- [x] 月度折線圖
- [x] 查詢面板移除 sl-details 收藏區
- [x] Header 新增檔案管理入口
- [x] 檔案管理獨立面板
