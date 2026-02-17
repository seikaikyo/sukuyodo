---
title: 配對吉日展示增強與時段建議
type: feature
status: completed
created: 2026-02-16
---

# 配對吉日展示增強與時段建議

## 變更內容

1. 配對吉日卡片從壓縮 chip 改為可展開卡片，顯示理由文字
2. 後端新增時段建議（推薦時段 + 避免時段）
3. 大吉/吉/中吉視覺差異強化

## 影響範圍

- `backend/services/sukuyodo.py` — 新增時段建議常數、修改 get_pair_lucky_days 回傳
- `frontend/src/components/LuckyDaysTab.vue` — 配對吉日卡片改版
- `frontend/src/composables/useSukuyodo.ts` — LuckyDay 型別新增欄位

## 測試計畫

1. curl 測試 pair-lucky-days API 回傳新欄位
2. 前端確認卡片展開/收合正常
3. 視覺確認大吉/吉/中吉差異明顯
