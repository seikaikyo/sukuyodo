---
title: 九曜星等級修正 + 理髮分類重構
type: fix
status: completed
created: 2026-02-16
---

# 九曜星等級修正 + 理髮分類重構

## 變更內容

### 1. 九曜星吉凶等級修正（以寺院原典為準）

三間寺院（放生寺、大聖院、岡寺）一致指出兩處等級錯誤：

| 星 | 現行 | 修正 | base_score |
|---|---|---|---|
| 水曜星 | 吉 (68) | 末吉 (58) | 68 → 58 |
| 月曜星 | 吉 (75) | 大吉 (80) | 75 → 80 |

依據：
- 岡寺原文 水曜星：「末吉なり貴人目上の人に引き立てられ幸ひ事多し」
- 岡寺原文 月曜星：「大吉にして信仰の人は竜の水を得たるが如く幸運なり」
- 放生寺：月曜星標為「悦三重の年」

### 2. 理髮從美容分類獨立

現狀問題：
- 理髮被歸在 `beauty`（美容）分類，與美甲、護膚混在一起
- 內容是美容院導向（「收集參考圖給設計師」）
- 用戶為真言宗阿闍梨，理髮（剃髮）是修行相關行為

修正：
- 將 `haircut` 從 `beauty` 分類移出，獨立為 `grooming` 分類
- 分類名稱：「身嗜み」（みだしなみ）
- 內容改寫為中性實用導向，兼顧修行者和一般人
- router 中「理髮」和「美容」的顯示名稱修正

### 3. router 命名修正

現狀：`hair_coloring` 顯示為「美容」→ 改為「染髮造型」

## 影響範圍

- `backend/services/sukuyodo.py` — KUYOU_STARS 資料修正 + LUCKY_DAY_CATEGORIES 分類重構 + 建議文案改寫
- `backend/routers/sukuyodo.py` — 吉日摘要項目名稱修正

## 測試計畫

1. 九曜：驗證 1977 年生 2026 年仍為日曜星(大吉)，確認水曜星/月曜星等級和分數已更新
2. 吉日 API：驗證 haircut 改為 grooming 分類後 API 回應正常
3. 現有前端不受影響（前端顯示 name 欄位，不依賴 category key）

## Checklist

- [ ] KUYOU_STARS 水曜星 level + base_score
- [ ] KUYOU_STARS 月曜星 level + base_score
- [ ] LUCKY_DAY_CATEGORIES 新增 grooming 分類
- [ ] beauty 分類移除 haircut
- [ ] haircut 建議文案改寫
- [ ] router 吉日摘要項目修正
- [ ] 測試驗證
