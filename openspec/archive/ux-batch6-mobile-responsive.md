---
title: 第六批 UX 改善：FortuneTab 和 LuckyDaysTab mobile 響應式
type: feature
status: completed
created: 2026-02-16
---

# 第六批 UX 改善：mobile 響應式補齊

## 變更內容

### 1. FortuneTab mobile 響應式

目前完全沒有 `@media (max-width: 767px)` 規則。需要：
- 幸運資訊 (lucky-info) 改為單欄
- 每日概覽 (daily-list) 改為可滑動
- 年運月趨勢 (trend-list) 字型縮小
- 分類描述 (category-descriptions) 改為單欄
- 三期秘曆 header wrap

### 2. LuckyDaysTab mobile 響應式

- 選日曆注 chips 改為 wrap
- 配對吉日 compatibility-row 改為 stack
- 圖例卡片適配小螢幕

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `frontend/src/components/FortuneTab.vue` | 新增 mobile 媒體查詢 |
| `frontend/src/components/LuckyDaysTab.vue` | 新增 mobile 媒體查詢 |

## 測試計畫

1. Chrome DevTools 切換 mobile 寬度確認排版正確
2. 確認所有互動元素 touch target >= 44px
