---
title: 每日幸運方位/顏色/數字動態化
type: fix
status: completed
created: 2026-02-14
---

# 每日幸運方位/顏色/數字動態化

## 問題描述

`calculate_daily_fortune` 的幸運方位、顏色、數字只根據 `user_element`（本命宿元素）靜態對應，不考慮日期變化。畢宿（月性）使用者 37 天都是「西北、銀色、2/7」，失去每日占卜的意義。

## 變更內容

改為結合以下因素產生每日不同的幸運推薦：
- **當日宿元素** (`day_mansion.element`)：決定基礎方位/顏色
- **七曜元素** (`day_element`)：作為次要影響
- **本命宿元素** (`user_element`)：作為個人化修正
- 三者交互作用，每天產生不同組合

### 計算邏輯

1. **方位**：以當日宿元素為主，本命宿元素為輔，用相生關係決定最佳方位
2. **顏色**：以七曜元素為主，當日宿元素為輔，產生每日不同的幸運色
3. **數字**：以當日宿 index 與七曜組合，產生每日不同的幸運數字

## 影響範圍

| 檔案 | 修改內容 |
|------|---------|
| `backend/services/sukuyodo.py` | `calculate_daily_fortune` 的 lucky 計算邏輯（~L803-807） |

共 1 個檔案，修改約 20-30 行。

## 測試計畫

1. 驗證連續 7 天的方位/顏色/數字都不同
2. 確認同一天同一人結果一致（隨機種子不變）
3. 確認前端顯示正常
4. 重新產生 fortune-calendar.html 驗證

## Checklist

- [x] 修改 calculate_daily_fortune 的 lucky 計算邏輯
- [x] 驗證每日結果有變化
- [x] 重新產生 fortune-calendar.html
- [x] 前端建構成功
