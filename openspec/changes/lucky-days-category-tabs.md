---
title: 吉日分類頁籤 + 使用者自選顯示
type: feature
status: completed
created: 2026-02-22
---

# 吉日分類頁籤 + 使用者自選顯示

## 變更內容

現狀：宿曜吉日區塊一次列出 8 個動作（求職面試、簽約、搬家…），無法自訂。
改為：依 9 大分類顯示頁籤，使用者可選擇要看的分類，偏好存入 localStorage。

後端已定義 9 大分類 / 34 個動作：
| 分類 | 動作數 | 內容 |
|------|--------|------|
| career 事業 | 4 | 面試、離職、開業、簽約 |
| study 學業 | 3 | 入學、考試、補習 |
| housing 居住 | 3 | 搬家、裝潢、購屋 |
| marriage 婚姻 | 3 | 登記、婚禮、訂婚 |
| medical 醫療 | 3 | 手術、健檢、看診 |
| travel 旅行 | 2 | 出國、旅遊 |
| grooming 剃髮 | 1 | 剃髮 |
| beauty 美容 | 5 | 染髮、燙髮、美甲、護膚、紋繡 |
| dating 感情 | 4 | 約會、告白、相親、分手 |
| shopping 購物 | 3 | 買衣服、買首飾、大額消費 |

## 設計方案

### 後端
- 修改 `/lucky-days/summary/{date_str}` 端點，回傳所有分類（grouped by category）
- 回傳結構改為 `categories: [{ key, name, actions: [{ action, name, lucky_days }] }]`

### 前端
- 宿曜吉日區塊改為分類頁籤（chip 風格，可多選）
- 預設啟用：事業、醫療、旅行、剃髮、購物（5 個）
- 使用者可切換分類，偏好存入 profile store（localStorage）
- 修行者模式：預設啟用 grooming（剃髮），不啟用 beauty

## 影響範圍
- `backend/routers/sukuyodo.py` — summary 端點回傳結構
- `frontend/src/components/LuckyDaysTab.vue` — 分類頁籤 UI
- `frontend/src/composables/useSukuyodo.ts` — 型別定義
- `frontend/src/stores/profile.ts` — 分類偏好儲存

## 測試計畫
1. API 回傳所有分類，結構正確
2. 前端分類頁籤可切換，偏好持久化
3. 修行者模式預設不顯示 beauty
4. npm run build 通過
