---
title: 每日運勢各項分述加入文字說明
type: feature
status: completed
created: 2026-02-16
---

# 每日運勢各項分述

## 背景

目前每日運勢的事業/感情/健康/財運只顯示數字分數，沒有任何文字說明。使用者無法理解數字背後的意義。需要加入基於宿曜經三九秘法的專業文字描述。

## 變更內容

### Backend

在 `calculate_daily_fortune` 回傳中，為每個分類加入文字說明：
- 說明根據「本命宿 x 當日宿關係」+「七曜元素」+「分數區間」動態生成
- 每個分類有 5 個等級的描述池，根據分數選擇
- 描述融入宿曜經元素（三九秘法關係、五行、七曜影響）

### Frontend

在每個分數條下方顯示對應的文字說明。

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `backend/services/sukuyodo.py` | 新增各項運勢描述池，回傳加入文字 |
| `frontend/src/components/FortuneTab.vue` | 分數條下方顯示描述 |
| `frontend/src/composables/useSukuyodo.ts` | DailyFortune 型別更新 |

## 測試計畫

1. curl API 確認回傳含 description 欄位
2. 不同分數區間顯示不同描述
3. 前端正確顯示
