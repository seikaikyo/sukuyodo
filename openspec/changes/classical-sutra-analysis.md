---
title: 原典三九秘法分析區塊
type: feature
status: completed
created: 2026-03-01
---

# 原典三九秘法分析區塊

## 變更內容

在相性（compatibility）結果中新增「原典分析」區塊，提供三層解讀：

1. **三九法位置展開**：展示雙方在對方三九法中的具體位置（第幾九、什麼位）
2. **原典經文引用**：直接引用 T21n1299 對應位置的經文原文
3. **白話解讀**：用現代語言解釋經文在這段關係中的意義

目前系統的相性結果直接跳到分數和現代描述，缺少「為什麼是這個關係」的原典根據。
用戶反饋：先看原典位置、再看經文、最後白話解讀，這個流程最能產生信任感。

## 設計原則

- 不改動現有分數系統，純粹新增一個平行的原典解讀層
- 經文出處標註到品/頁碼（如 T21, p.391b）
- 雙向分析：A 看 B 是什麼位、B 看 A 是什麼位，兩邊都要講

## 影響範圍

### 後端
- `backend/services/sukuyodo.py`：新增 `get_classical_analysis(index1, index2)` 方法
- `backend/services/sukuyodo.py`：`calculate_compatibility()` 回傳中新增 `classical` 欄位
- `backend/data/sukuyodo_mansions.json`：relations 區塊補充各位置的經文原文和白話

### 前端
- `frontend/src/components/MatchTab.vue`：新增「原典分析」摺疊面板
- `frontend/src/composables/useSukuyodo.ts`：TypeScript 型別擴展

## 資料結構設計

### API 回傳新增欄位（在 compatibility data 中）

```json
{
  "classical": {
    "source": "T21n1299 品第三 序三九祕宿品",
    "person1_view": {
      "target_position": "三九之安",
      "nine_group": 3,
      "nine_group_name": "胎行",
      "position_name": "安",
      "position_reading": "あん",
      "sutra_text": "安日，移徙吉，遠行人入宅、造作園宅、安坐臥床帳、作壇場並吉。",
      "sutra_ref": "T21, p.397c-398a",
      "interpretation": "你看對方落在「安」位——安定、穩固的位置。你對這個人的直覺是安全的、可以靠近的。"
    },
    "person2_view": {
      "target_position": "一九之壊",
      "nine_group": 1,
      "nine_group_name": "命行",
      "position_name": "壊",
      "position_reading": "かい",
      "sutra_text": "壞日，宜作鎮壓、降伏怨讎及討伐阻壞奸惡之謀，餘並不堪。",
      "sutra_ref": "T21, p.397c-398a",
      "interpretation": "對方看你落在「壊」位——你的存在對他帶有破壞性。這不是你的問題，是位置的結構。"
    },
    "reversal_note": {
      "sutra_text": "若犯衰、危、壞等宿者，則所求稱意、百事通達。",
      "sutra_ref": "T21, p.391b-c",
      "applies": true,
      "interpretation": "凌犯逆轉法則：當衰/危/壊位被犯時，反而百事通達。"
    }
  }
}
```

### 九位經文對照表（寫入 sukuyodo_mansions.json 的 relations 區塊）

| 位置 | 經文原文 | 出處 |
|------|---------|------|
| 命 | 命宿直日，不宜舉動百事 | T21, p.391b |
| 栄 | 榮宿日，宜入官拜職、對見大人...並大吉 | T21, p.397c |
| 衰 | 若衰日，唯宜解除諸惡、療病 | T21, p.398a |
| 安 | 安日，移徙吉，遠行人入宅、造作園宅...並吉 | T21, p.397c |
| 危 | 危壞日，並不宜遠行出、入移徙...並凶 | T21, p.398a |
| 成 | 成宿日，宜修道學問、合和長年藥法...並吉 | T21, p.398a |
| 壊 | 壞日，宜作鎮壓、降伏怨讎及討伐...餘並不堪 | T21, p.398a |
| 友 | 友宿日、親宿日，宜結交、定婚姻...並吉 | T21, p.398a |
| 親 | 友宿日、親宿日，宜結交、定婚姻...並吉 | T21, p.398a |
| 業 | 值業宿日，所作善惡亦不成就，甚衰 | T21, p.398a |
| 胎 | 命宿日、胎宿日，不宜舉動百事 | T21, p.398a |

## 前端 UI 規格

- 放在相性結果頁面，位於現有「關係說明」之後
- 使用 PrimeVue `<Panel>` 元件，預設展開
- 標題：「原典三九秘法」
- 內部分兩欄：A 視角 / B 視角
- 經文用 `<blockquote>` 樣式，出處用小字標註
- 白話解讀用一般文字
- 間距: 16px (4px 倍數)
- 響應式: mobile 改為單欄堆疊

## 測試計畫

1. 驗證 27x27=729 種組合的三九法位置計算是否正確
2. 用 CBETA 原典景風註例（畢宿）交叉驗證
3. 經文引用出處與 cbeta_t21n1299_reference.md 比對
4. 前端 mobile/desktop 顯示正常
5. API 回應時間不增加超過 50ms

## Checklist

- [x] 後端 `get_classical_analysis()` 方法
- [x] 九位經文常數資料
- [x] 白話解讀文案（11 個位置含命/業/胎）
- [x] `calculate_compatibility()` 整合
- [x] 前端 TypeScript 型別
- [x] 前端 MatchTab.vue 原典面板（個人+公司）
- [x] 景風註例驗證（畢→觜=一九之栄、畢→壁=三九之危）
- [x] API 回應格式確認（含同宿/業/胎邊界）
