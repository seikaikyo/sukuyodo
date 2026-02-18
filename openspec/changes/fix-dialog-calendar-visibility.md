---
title: 修復查詢對話框遮罩問題與月曆吉凶凌犯可見度
type: fix
status: completed
created: 2026-02-18
---

# 修復查詢對話框遮罩問題與月曆吉凶凌犯可見度

## 變更內容

### Bug 1: 查詢對話框被自訂遮罩蓋住
- `.dialog-backdrop` z-index 600 遮住了 Shoelace dialog
- 用戶開啟查詢後整個畫面變黑，對話框不可見/不可操作
- 根因：最近五次 commit 反覆修改遮罩方案仍未解決

**修正方案**：移除自訂遮罩，改用 Shoelace 內建 overlay 搭配正確的 CSS 變數覆寫

### Bug 2: 月曆凌犯期間幾乎看不見
- `--ryouhan-bg: rgba(255, 100, 100, 0.12)` 透明度太低
- 凌犯日期格子沒有文字標籤，只靠微弱背景色
- `--dark-week-bg: rgba(0, 0, 0, 0.25)` 對比度不足

**修正方案**：提高凌犯/暗黑週背景透明度，在日期格子加入「凌犯」文字標籤

### Bug 3: 特殊日標籤太小
- 甘露/金剛/羅刹標籤 8px 字級難以辨識

**修正方案**：放大標籤字級與間距

## 影響範圍
- `frontend/src/views/HomeView.vue` - 移除自訂 backdrop，修正對話框 z-index
- `frontend/src/components/FortuneCalendar.vue` - 加入凌犯標籤、放大特殊日標籤
- `frontend/src/styles/variables.css` - 調整 ryouhan-bg 和 dark-week-bg 透明度

## 測試計畫
1. 開啟查詢對話框 - 遮罩顯示正常，對話框可操作
2. 點擊遮罩或取消 - 對話框正常關閉
3. 執行查詢 - 對話框關閉，結果正確顯示
4. 檢視月曆 - 凌犯日期背景明顯可辨
5. 檢視月曆 - 凌犯日期格子有「凌犯」文字標籤
6. 檢視月曆 - 暗黑週日期背景有明顯區分
7. 檢視月曆 - 甘露/金剛/羅刹標籤清晰可讀

## Checklist
- [ ] 移除自訂 dialog-backdrop
- [ ] 修正 Shoelace overlay 樣式
- [ ] 提高 ryouhan-bg 透明度
- [ ] 提高 dark-week-bg 透明度
- [ ] 在凌犯日期加入文字標籤
- [ ] 放大特殊日標籤字級
- [ ] 視覺驗證
