---
title: 流年報告 / 相性報告 / 雙人流年報告 HTML 匯出
type: feature
status: completed
created: 2026-02-16
---

# 流年報告 / 相性報告 / 雙人流年報告 HTML 匯出

## 變更內容

純前端生成可離線閱讀的 HTML 報告，三種報告分開匯出：
- 流年報告：依當前世俗觀/修行者觀視角匯出十年流年資料
- 相性報告：匯出完整相性診斷結果
- 雙人流年報告：並列比較雙方十年流年走勢（含雙線圖、互補分析、逐年月運）

## 影響範圍

- `frontend/src/utils/report-generator.ts`（新增 generatePairedDecadeReport）
- `frontend/src/components/FortuneTab.vue`（新增 props + 匯出按鈕）
- `frontend/src/components/MatchTab.vue`（新增雙人流年匯出按鈕 + birthDate prop）
- `frontend/src/views/HomeView.vue`（傳入 mansion/birthDate props）

## 測試計畫

1. 流年 tab 匯出按鈕觸發下載
2. 世俗觀和修行者觀各自匯出正確內容
3. 相性 tab 匯出按鈕觸發下載
4. 相性結果區「匯出雙人流年」按鈕觸發 API 呼叫 + 下載
5. HTML 報告獨立開啟正常顯示
6. 雙線走勢圖兩條線正確（amber + 天藍）
7. 逐年月運圖雙線正確
8. 互補分析數據正確
9. 列印預覽正常（白底黑字）
10. TypeScript 編譯無錯誤

## Checklist

- [x] report-generator.ts 共用 CSS + 下載工具
- [x] generateDecadeReport() 流年報告生成
- [x] generateCompatReport() 相性報告生成
- [x] generatePairedDecadeReport() 雙人流年報告生成
- [x] FortuneTab 匯出按鈕
- [x] MatchTab 相性匯出按鈕
- [x] MatchTab 雙人流年匯出按鈕
- [x] HomeView 傳 birthDate 給 MatchTab
- [x] @media print 列印友善樣式
- [x] TypeScript 編譯通過
