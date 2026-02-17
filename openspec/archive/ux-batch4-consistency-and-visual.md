---
title: 第四批 UX 改善：視覺一致性與摘要卡片
type: feature
status: completed
created: 2026-02-16
---

# 第四批 UX 改善：視覺一致性與摘要卡片

## 變更內容

### 1. 元素關係區塊加背景框

方向解釋有 `direction-box` 背景框，但元素關係沒有。統一視覺層級。

### 2. 特殊日說明重點強調

「不分本命宿，所有人共通」等重要訊息加 strong 標記。

### 3. SummaryCard 宿曜關係拆行

「今日與本命宿關係」長文字在 mobile 上易換行且難讀，拆為標題行+描述行。

### 4. 配對吉日相性資訊排版優化

相性分數區塊在 mobile 上擁擠，改善間距和 score bar 視覺化。

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `frontend/src/components/MatchTab.vue` | 元素關係背景框 |
| `frontend/src/components/LuckyDaysTab.vue` | 特殊日說明 + 配對相性排版 |
| `frontend/src/components/SummaryCard.vue` | 宿曜關係拆行 |

## 測試計畫

1. 瀏覽器確認元素關係有背景框
2. 瀏覽器確認特殊日說明重點加粗
3. 瀏覽器確認 SummaryCard 關係文字易讀
4. 瀏覽器確認配對吉日相性資訊排版整潔
