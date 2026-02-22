---
title: 日曆 .ics 匯出功能
type: feature
status: completed
created: 2026-02-22
---

# 日曆 .ics 匯出功能

## 變更內容

在年曆頁面新增「匯出日曆」按鈕，產生 iCalendar (.ics) 格式檔案，讓用戶可匯入 Apple Calendar 或 Google Calendar。

### 使用流程
```
輸入生日 → 系統算出本命宿 → 看年曆 → 按「匯出日曆」→ 下載 .ics → 匯入日曆 App
```

### 匯出內容（每日全天事件）

**標題格式**: `【{等級}】{宿名}({五行}) - {七曜日} {特殊標記}`
- 特殊標記: 甘露日/金剛峯日/羅刹日/凌犯期間/剃髮吉日

**描述欄位**:
- 關係類型 + 運勢分數
- 四維分數（事業/感情/健康/財運）
- 三期狀態（躍動の週/破壊の週/再生の週）
- 特殊日說明（適宜/不宜事項）
- 凌犯期間警示
- 暗黒の一週間標記
- 幸運色/方位/數字

### 檔名格式
`sukuyodo_{年份}_{宿名}_{出生日期}.ics`
例: `sukuyodo_2026_觜宿_19771029.ics`

## 技術方案

### 純前端實作，不動後端

使用 JavaScript 在瀏覽器端組 iCalendar 字串，觸發下載。不需安裝額外套件，iCalendar 格式簡單可手寫。

### 資料來源

逐月呼叫現有 API `/api/sukuyodo/calendar/monthly/{year}/{month}?birth_date=YYYY-MM-DD`，取得 12 個月的完整日曆資料後組成 .ics。

## 影響範圍

- `frontend/src/components/FortuneTab.vue` - 年曆 tab 新增匯出按鈕
- `frontend/src/utils/ics-generator.ts` - 新增 .ics 產生工具（新檔案）
- `frontend/src/composables/useSukuyodo.ts` - 新增 fetchFullYearCalendar 函式

## 測試計畫

1. 匯出 .ics 檔案，確認格式正確（RFC 5545）
2. 匯入 Apple Calendar，確認事件顯示正確
3. 匯入 Google Calendar，確認事件顯示正確
4. 換不同生日查詢後匯出，確認內容隨本命宿改變
5. 確認檔名包含年份、宿名、出生日期

## Checklist

- [x] 建立 ics-generator.ts 工具函式
- [x] useSukuyodo.ts 新增 fetchFullYearCalendar
- [x] FortuneTab.vue 年曆 tab 加匯出按鈕
- [x] HomeView.vue 傳遞 prop
- [ ] 測試 Apple Calendar 匯入
- [ ] 測試 Google Calendar 匯入
