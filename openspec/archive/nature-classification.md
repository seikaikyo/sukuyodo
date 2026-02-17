---
title: 二十七宿性質分類（七科分宿）
type: feature
status: completed
created: 2026-02-17
---

# 二十七宿性質分類（七科分宿）

## 變更內容
依據宿曜經原典，新增 27 宿的七科分宿（性質分類）欄位與詳細說明。
Phase 1 已完成 nature_type 欄位和 badge 顯示。
Phase 2 新增 7 種分類的專業說明和獨立知識 tab。

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
- `backend/data/sukuyodo_mansions.json` — 每宿 `nature_type` 欄位 + metadata 內 `nature_types_knowledge`
- `backend/routers/sukuyodo.py` — `/mansions` 端點加入 nature_type
- `frontend/src/composables/useSukuyodo.ts` — Mansion interface + Metadata interface
- `frontend/src/components/KnowledgeTab.vue` — nature badge + 七科分宿知識 tab

## 測試計畫
1. API `/metadata` 回傳含 nature_types_knowledge
2. 前端「七科分宿」tab 顯示 7 個分類卡片
3. 本命宿所屬分類正確標示

## Checklist
- [x] JSON 資料新增 nature_type (Phase 1)
- [x] 後端 /mansions 端點加入 nature_type (Phase 1)
- [x] 前端 Mansion interface + nature badge (Phase 1)
- [x] JSON metadata 新增 nature_types_knowledge
- [x] 前端 Metadata interface 擴充
- [x] 前端七科分宿知識 tab
