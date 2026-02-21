---
title: 統一日本字體術語
type: fix
status: completed
created: 2026-02-21
---

# 統一日本字體術語

## 變更內容

將系統中混用的繁體中文字體統一為日本漢字（高野山真言宗儀軌標準）：

| 繁中(混用) | 日本字體(統一) | 類型 |
|---|---|---|
| 安壞 | 安壊 | 六種關係名 |
| 壞方/壞者 | 壊方/壊者 | 安壊中的角色 |
| 壞宿/壞日 | 壊宿/壊日 | 三九法日型 |
| 榮親 | 栄親 | 六種關係名 |
| 暗黑 | 暗黒 | 暗黒の一週間 |

排除範圍：
- `cbeta_t21n1299_reference.md`（原典照錄，不改）
- `openspec/archive/*`（歷史紀錄，不改）
- 自然語意的「壞」（壞事、壞習慣、好壞等）不改

## 影響範圍
- `backend/services/sukuyodo.py`
- `backend/data/sukuyodo_mansions.json`
- `backend/routers/sukuyodo.py`
- `frontend/src/components/MansionWheel.vue`
- `frontend/src/components/FortuneTab.vue`

## 測試計畫
1. API 端點回應中的關係名稱正確顯示為日本字體
2. 前端頁面顯示正確
3. 計算邏輯不受影響（僅改顯示文字，不改 key/enum）
