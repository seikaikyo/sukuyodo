---
title: 流年報告 / 相性報告 HTML 匯出
type: feature
status: in-progress
created: 2026-02-16
---

# 流年報告 / 相性報告 HTML 匯出

## 變更內容

純前端生成可離線閱讀的 HTML 報告，兩種報告分開匯出：
- 流年報告：依當前世俗觀/修行者觀視角匯出十年流年資料
- 相性報告：匯出完整相性診斷結果

## 影響範圍

- `frontend/src/utils/report-generator.ts`（新增）
- `frontend/src/components/FortuneTab.vue`（新增 props + 匯出按鈕）
- `frontend/src/components/MatchTab.vue`（新增匯出按鈕）
- `frontend/src/views/HomeView.vue`（傳入 mansion/birthDate props）

## 測試計畫

1. 流年 tab 匯出按鈕觸發下載
2. 世俗觀和修行者觀各自匯出正確內容
3. 相性 tab 匯出按鈕觸發下載
4. HTML 報告獨立開啟正常顯示
5. 列印預覽正常（白底黑字）
6. TypeScript 編譯無錯誤

## Checklist

- [ ] report-generator.ts 共用 CSS + 下載工具
- [ ] generateDecadeReport() 流年報告生成
- [ ] generateCompatReport() 相性報告生成
- [ ] FortuneTab 匯出按鈕
- [ ] MatchTab 匯出按鈕
- [ ] @media print 列印友善樣式
- [ ] TypeScript 編譯通過
