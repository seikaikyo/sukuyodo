---
title: 運勢資料顯示補完
type: feature
status: completed
created: 2026-02-16
---

# 運勢資料顯示補完

## 背景

API 回傳了大量有用資料，前端卻沒有顯示。三個審查 agent 回報的 P1/P2 級問題中，大部分是「API 有資料、前端沒用到」。

## 變更內容

### 1. 年運勢：新增 12 月趨勢圖

API 的 `monthly_trend` 回傳 12 個月的分數和提示，目前完全沒顯示。
在年運勢的分數條和分類描述之間，新增一個 12 月趨勢列表，每月顯示分數條和提示。

### 2. 週運勢：顯示幸運色與幸運方位

API 回傳 `lucky.direction`、`lucky.color`、`lucky.color_hex`，前端沒有顯示。
復用每日運勢的 `.lucky-info` 樣式，在週運勢的分數條之後顯示。

### 3. 月運勢：顯示農曆月、當月宿、本月關係

API 回傳 `lunar_month`、`month_mansion`、`relation`，前端沒有顯示。
在月運勢標題下方新增一行宿曜資訊：農曆月 / 當月宿 / 與本命宿的關係。

### 4. 月運勢：補齊健康和財運分數

目前月運勢只顯示整體、事業、感情三個分數條，但 API 回傳五個。補上健康和財運。

### 5. 特殊日：使用 API 回傳的 description 取代硬編碼

LuckyDaysTab 的 `getSpecialDayAdvice()` 是前端硬編碼的建議文字。API 的 special-days 端點已經回傳 `description` 欄位，應該優先使用 API 的資料。

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `frontend/src/components/FortuneTab.vue` | 新增 monthly_trend 區塊、週運 lucky、月運宿曜資訊+健康財運分數 |
| `frontend/src/components/LuckyDaysTab.vue` | 特殊日 description 改用 API 資料 |
| `frontend/src/composables/useSukuyodo.ts` | WeeklyFortune 型別已有 lucky、MonthlyFortune 已有 lunar_month/relation（不需修改） |

## 測試計畫

1. pm2 restart 前端
2. 瀏覽器確認年運勢顯示 12 月趨勢
3. 瀏覽器確認週運勢顯示幸運色和方位
4. 瀏覽器確認月運勢顯示農曆月、當月宿、關係、五個分數
5. 瀏覽器確認特殊日顯示 API 回傳的描述
