---
title: 宿曜經原典日文與漢文經典對照
type: feature
status: in-progress
created: 2026-02-17
---

# 宿曜經原典日文與漢文經典對照

## 變更內容

在現有正體中文翻譯的基礎上，加入：
1. **漢文原典**：宿曜經（文殊師利菩薩及諸仙所説吉凶時日善悪宿曜経）原文摘錄
2. **日本寺院傳統詮釋**：放生寺/大聖院/岡寺等真言宗寺院的日文解說

搭配方式：原典 → 日文詮釋 → 正體中文說明

## 適用範圍

| 內容 | 檔案 | 預估欄位數 |
|------|------|-----------|
| 27宿性格描述 | sukuyodo_mansions.json | 27 × 5 = 135 |
| 六種關係說明 | sukuyodo_mansions.json | 6 × 2 = 12 |
| 五行七曜說明 | sukuyodo_mansions.json | 7 × 5 = 35 |
| 甘露/金剛/羅刹 | sukuyodo.py | 3 |
| 凌犯期間 | sukuyodo.py | 已有 description_ja |
| 九曜流年 | sukuyodo.py | 9 |
| 三期サイクル | sukuyodo.py | 已有 description_ja |
| 每日運勢建議 | sukuyodo.py | 30 |
| 月運勢建議 | sukuyodo.py | 30 |
| 週運焦點 | sukuyodo.py | 6 |

## 影響範圍

### 後端
- `backend/data/sukuyodo_mansions.json` - 新增 `*_ja` 和 `*_classic` 欄位
- `backend/services/sukuyodo.py` - 硬編碼字典新增日文欄位
- `backend/routers/sukuyodo.py` - API 回傳已包含的欄位自動帶出

### 前端
- `frontend/src/components/KnowledgeTab.vue` - 顯示三語對照
- `frontend/src/components/FortuneTab.vue` - 運勢日文顯示
- `frontend/src/components/SummaryCard.vue` - 摘要日文顯示
- `frontend/src/components/MatchTab.vue` - 相性日文顯示

## 資料結構設計

```json
{
  "personality": "正體中文說明...",
  "personality_ja": "日本寺院の伝統的解釈...",
  "personality_classic": "宿曜経原典：「...」"
}
```

## UI/UX 規格

- 預設顯示：正體中文（現有行為不變）
- 原典/日文以摺疊區塊呈現，點擊展開
- 使用 PrimeVue Fieldset 或 Panel 元件
- 經典原文用特殊字體樣式區分（如斜體或引用區塊）

## 分階段實作

### Phase 1: 資料結構 + 核心內容（本次）
- 建立 `_ja` / `_classic` 欄位結構
- 27宿性格描述（最核心、最常被閱讀的內容）
- 六種關係說明
- 特殊日/凌犯/九曜的經典引文
- 前端顯示元件

### Phase 2: 運勢建議內容（後續）
- 每日/週/月運勢建議 150+ 句的日文版本
- 五行七曜詳細說明

## 測試計畫

1. API 回傳包含新欄位（curl 驗證）
2. 前端正確顯示三語對照
3. 摺疊/展開互動正常
4. 行動裝置排版正確
5. 現有中文顯示不受影響

## Checklist
- [x] 資料結構設計（_ja / _classic 欄位）
- [x] 27宿日文原典內容
- [x] 六種關係日文原典
- [x] 特殊日/三期サイクル日文原典
- [x] 九曜流年日文原典
- [x] 前端顯示元件
- [x] 測試驗證（API + TypeScript）
