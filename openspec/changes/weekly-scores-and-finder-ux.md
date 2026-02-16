---
title: 週運分數補齊與相性 finder 易讀性
type: feature
status: completed
created: 2026-02-16
---

# 週運分數補齊與相性 finder 易讀性

## 變更內容

### 1. 週運勢補齊健康和財運分數

週運勢目前只顯示整體、事業、感情三個分數條，但 API 回傳五個。補上健康和財運。

### 2. 相性 finder 加入簡介說明

尋找配對頁面直接顯示六種關係分組，沒有前置說明。加入一段簡短說明讓使用者理解：
- 六種關係是什麼
- 分數代表什麼意義
- 距離分類（近/中/遠）的概念

### 3. 相性 finder 顯示農曆日期

每個宿的 mansion chip 旁邊顯示對應的農曆日期範圍，讓使用者能對照實際生日。

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `frontend/src/components/FortuneTab.vue` | 週運勢補齊 2 個分數條 |
| `frontend/src/components/MatchTab.vue` | finder 簡介 + 農曆日期顯示 |

## 測試計畫

1. 瀏覽器確認週運勢顯示五個分數
2. 瀏覽器確認 finder 頁面有簡介
3. 瀏覽器確認每個宿顯示農曆日期
