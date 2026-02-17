---
title: 二十七宿性質分類（七科分宿）
type: feature
status: completed
created: 2026-02-17
---

# 二十七宿性質分類（七科分宿）

## 變更內容
依據宿曜經原典，新增 27 宿的七科分宿（性質分類），將每宿歸入 7 種性質類別之一。
6 個外部來源交叉驗證完全一致，無爭議。

## 七科分類

| 分類 | 宿數 | 所屬宿 | 梵文對應 |
|------|------|--------|---------|
| 安住宿 | 4 | 畢、翼、斗、壁 | Dhruva (固定) |
| 和善宿 | 4 | 觜、角、房、奎 | Mridu (柔和) |
| 悪害宿 | 4 | 参、柳、心、尾 | Ugra (猛烈) |
| 急速宿 | 4 | 鬼、軫、婁、胃 | Kshipra (迅速) |
| 猛悪宿 | 4 | 星、張、箕、室 | Tikshna (鋭利) |
| 軽燥宿 | 5 | 井、亢、女、虚、危 | Chara (移動) |
| 剛柔宿 | 2 | 昴、氐 | Mishra (混合) |

## 影響範圍
- `backend/data/sukuyodo_mansions.json` — 每宿新增 `nature_type` 欄位
- `backend/services/sukuyodo.py` — 新增 NATURE_TYPE 常數和 API 支援
- 前端宿詳情頁 — 顯示性質分類

## 測試計畫
1. 驗證 27 宿的 nature_type 全部正確對應
2. API 回傳包含 nature_type
3. 前端正確顯示

## Checklist
- [x] JSON 資料新增 nature_type (27 宿全部正確)
- [x] 後端 /mansions 端點加入 nature_type
- [x] 前端 Mansion interface 加入 nature_type
- [x] 前端 KnowledgeTab 顯示 nature-badge
