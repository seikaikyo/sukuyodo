---
title: 第五批 UX 改善：日文讀音顯示與月運關係說明
type: feature
status: completed
created: 2026-02-16
---

# 第五批 UX 改善：日文讀音顯示與月運關係說明

## 變更內容

### 1. 月運關係說明文字

月運 API 回傳 `relation.description` 和 `relation.reading`，但前端只顯示 `relation.name`。
補上 description 和 reading（ruby 注音）。

### 2. 每日運勢三期日型日文讀音

三九秘曆的 period 和 day_type 有 reading（如「再生の週」→「さいせいのしゅう」），
以 ruby 注音方式顯示。

### 3. 每日幸運方位/幸運色日文讀音

幸運方位「南」有 reading「みなみ」，幸運色「銀色」有 reading「ぎんいろ」。
以 ruby 注音方式在日文原文旁邊顯示。

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `frontend/src/components/FortuneTab.vue` | 月運 relation + 三期讀音 + 幸運讀音 |

## 測試計畫

1. 瀏覽器確認月運顯示關係說明文字
2. 瀏覽器確認三期秘曆有 ruby 讀音
3. 瀏覽器確認幸運資訊有 ruby 讀音
