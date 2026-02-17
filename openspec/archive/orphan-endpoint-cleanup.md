---
title: 孤兒API端點清理
type: refactor
status: completed
created: 2026-02-17
---

# 孤兒 API 端點清理

## 變更內容
移除 6 個無前端呼叫者的後端 API 端點，以及 3 個隨之成為孤兒的 service 方法。

### 移除端點
1. `/formula` — 靜態計算公式說明，知識已在前端元件內
2. `/career-guidance/{date}` — 求職指引，已被 summary 涵蓋
3. `/lucky-days/categories` — 吉日類別清單，前端改用 summary 一次取得
4. `/lucky-days/{date}` — 單類別吉日查詢，被 summary 取代
5. `/calendar/day/{date}` — 單日曆注，前端用月曆端點
6. `/calendar/upcoming` — 未來吉日列表，前端用月曆翻頁

### 移除 service 方法（僅被上述端點呼叫）
- `sukuyodo.get_career_guidance()` + 相關資料常數
- `sukuyodo.get_all_lucky_day_categories()`
- `japanese_calendar.get_upcoming_lucky_days()`

### 保留的方法（有其他呼叫者）
- `sukuyodo.get_lucky_days()` — `/lucky-days/summary` 使用
- `japanese_calendar.get_day_info()` — 月曆端點內部使用

## 影響範圍
- `backend/routers/sukuyodo.py` — 移除 6 個路由
- `backend/services/sukuyodo.py` — 移除 2 個方法 + 相關常數
- `backend/services/japanese_calendar.py` — 移除 1 個方法

## 測試計畫
1. 後端啟動無錯誤
2. 保留的端點 `/lucky-days/summary` 和 `/calendar/lucky-days` 正常運作
3. 前端功能不受影響

## Checklist
- [x] 移除 6 個路由端點
- [x] 移除 3 個孤兒 service 方法 + CAREER_BY_ELEMENT 常數 + _get_career_advice 方法
- [x] 驗證後端啟動正常
- [x] 驗證保留端點正常運作
