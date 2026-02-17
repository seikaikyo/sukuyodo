---
title: 宿曜道運算正確性修正
type: fix
status: completed
created: 2026-02-14
completed: 2026-02-14
---

# 宿曜道運算正確性修正

## 變更內容

根據完整的宿曜道規則驗證，修正 3 個 Bug 和 2 個設計問題。

### BUG 1：日干支地支偏移修正（嚴重）

1900-01-01 實際為甲戌日（地支=10），程式碼誤設為甲子日（地支=0），導致所有地支相關判定偏移 10 位。修正後一粒萬倍日、天赦日、寅の日、巳の日、己巳の日全部連帶修正。

**修正：** `branch = (days + 10) % 12`

### BUG 2：月運勢使用西曆月份查詢農曆月宿（嚴重）

`MONTH_START_MANSION` 是農曆月份表，但直接以西曆月份查詢。

**修正：** 取該西曆月份中間日（15 日）轉農曆，用農曆月份查詢月宿。

### BUG 3：不成就日八月資料錯誤（中等）

傳統不成就日為 6 個月循環（2=8），八月應為 `[2, 10, 18, 26]`。

### 設計改進：移除犯太歲功能

犯太歲是中國年運觀念，宿曜道原典（《宿曜經》）中並無此概念。移除犯太歲檢查邏輯和 `mansion_range` 欄位，保留生肖基本資料供年運勢天干地支顯示。

### 設計改進：日/月元素使用 special_elements 資料

改用 `sukuyodo_fortune.json` 中已定義的 `special_elements` 資料：日僅生火（+10）、月僅生水（+10），其餘為中性（0）。

## 影響範圍

- `backend/services/japanese_calendar.py:103` - 地支計算加偏移 +10
- `backend/services/japanese_calendar.py:78` - 不成就日八月資料
- `backend/services/sukuyodo.py:893-895` - 月運勢轉農曆月份
- `backend/services/sukuyodo.py:654-658` - 日/月元素 special_elements
- `backend/data/sukuyodo_fortune.json:143-155` - 移除 mansion_range
- `backend/services/sukuyodo.py:1191-1240` - 移除犯太歲檢查邏輯

## 驗證結果

1. 日干支：2026-02-14 計算為己未，與萬年曆一致
2. 月運勢：2026 年 1 月（農曆十一月）正確查到斗宿(index=7)
3. 不成就日：2026 年 8 月為 2, 10, 18, 26 日
4. 元素關係：日+火=相生(+10)、月+水=相生(+10)、日+金=中性(0)、月+土=中性(0)
5. 回歸測試：每日運勢、雙人相性、年運勢 API 均正常

## Checklist

- [x] BUG 1: 日干支地支偏移修正
- [x] BUG 2: 不成就日八月資料修正
- [x] BUG 3: 月運勢農曆月份修正
- [x] 設計改進: 移除犯太歲功能
- [x] 設計改進: 日/月元素 special_elements
- [x] 回歸測試通過
