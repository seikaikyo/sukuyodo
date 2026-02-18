---
title: 月曆可讀性提升與查詢對話框溢出修正
type: fix
status: completed
created: 2026-02-18
---

# 月曆可讀性提升與查詢對話框溢出修正

## 變更內容

### 問題 1：月曆格子資訊密度不足、可讀性差
- 宿名字體 10-11px 在深色背景下難辨識
- 特殊日標籤（甘/金/羅）8px 太小
- 運勢圓點 6-8px 不夠顯眼
- 格子間距 2px 太窄，視覺上黏在一起
- 日本選日標籤 7px 幾乎看不到

**改善方案：**
- 增大格子最低高度（56→64 mobile, 80→90 desktop）
- 放大宿名字體（10→11 mobile, 11→12 desktop）
- 放大特殊日標籤（8→9 mobile, 9→10 desktop）
- 運勢圓點放大（6→8 mobile, 8→10 desktop）
- 格子間距 2px→3px
- 日本選日標籤放大（7→8 mobile, 8→9 desktop）
- 增加格子內 padding

### 問題 2：查詢本命宿對話框底部按鈕被截斷
- 收藏對象清單+表單撐高內容，超出視窗高度
- sl-dialog 預設無內容捲動，footer 按鈕被推出可視範圍

**改善方案：**
- 對 `.query-content` 設定 `max-height` + `overflow-y: auto`
- 限制對話框最大高度為 `80vh`

## 影響範圍
- `frontend/src/components/FortuneCalendar.vue`（樣式調整）
- `frontend/src/views/HomeView.vue`（對話框樣式調整）

## 測試計畫
1. 確認月曆各元素字體放大後不溢出格子
2. 確認手機版（< 768px）和桌面版都正常
3. 確認查詢對話框在收藏對象多的情況下可捲動
4. 確認對話框 footer 按鈕始終可見

## Checklist
- [ ] FortuneCalendar.vue 樣式調整
- [ ] HomeView.vue 對話框樣式調整
- [ ] 響應式測試
