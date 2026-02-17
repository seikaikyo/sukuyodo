---
title: 真言宗修行對照指南
type: feature
status: completed
created: 2026-02-16
---

# 真言宗修行對照指南

## 變更內容

在流年功能加入世俗觀/修行者觀雙視角切換。修行者視角以空海大師《宿曜經》為本，
九曜不是趨吉避凶的工具，而是修行時機的指引。大凶年對行者而言是最佳精進期。

切換後整個流年頁面的語氣、建議、分類描述、月度指引全部替換為修行者視角。

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `backend/services/sukuyodo.py` | 新增 SHINGON_PRACTICE_DATA（9 星修行資料）、SHINGON_ADVICE/THEME/CATEGORY 常數、calculate_yearly_fortune 加入 shingon 欄位 |
| `backend/routers/sukuyodo.py` | yearly-range 端點不變（資料自動包含 shingon 欄位） |
| `frontend/src/components/FortuneTab.vue` | 流年 tab 加入視角切換 toggle、根據視角切換所有內容 |
| `frontend/src/composables/useSukuyodo.ts` | YearlyFortune 型別擴充 shingon 欄位 |

## 設計規格

### 修行者視角資料結構（每顆九曜星）

```python
SHINGON_PRACTICE_DATA = {
    "羅喉星": {
        "practice_name": "閉關沉潛期",
        "practice_level": "精進",
        "core_teaching": "空海大師教言...",
        "practice_focus": "修行重心描述",
        "recommended_practices": ["持咒精進", "減少外緣", ...],
        "mantra": { "name": "真言名", "text": "梵文", "reading": "讀音" },
        "homa_type": "息災護摩",
        "category_practice": {
            "career": "法務觀...",
            "love": "慈悲行觀...",
            "health": "身心調和觀...",
            "wealth": "福德觀..."
        },
        "monthly_guide": "12 個月修行節奏...",
        "warnings": ["修行注意事項"],
        "opportunities": ["修行好時機"]
    }
}
```

### 修行者視角分類對應

| 世俗分類 | 修行者分類 | 說明 |
|----------|-----------|------|
| 事業 | 法務/弘法 | 以利他為本的事業觀 |
| 感情 | 慈悲行 | 以慈悲為本的人際觀 |
| 健康 | 身心調和 | 以禪定為本的養生觀 |
| 財運 | 福德/供養 | 以布施為本的財物觀 |

### 吉凶等級對應

| 世俗等級 | 修行者等級 | 色標 |
|----------|-----------|------|
| 大吉 | 弘法利生期 | 金色（同既有） |
| 吉 | 精進增上期 | 綠色（同既有） |
| 半吉 | 穩固調和期 | 藍色（同既有） |
| 大凶 | 閉關精進期 | 紫色（取代紅色） |

### 前端 Toggle 規格

- 位置：流年 tab 頂部，年份導覽下方
- 樣式：兩個 pill button（世俗觀 / 修行者觀）
- 預設：世俗觀
- 切換時不重新 fetch（資料已包含兩套）

## 測試計畫

1. API 回傳包含 shingon 欄位
2. 世俗觀不受影響（向下相容）
3. 修行者觀正確顯示所有替換內容
4. Toggle 切換即時生效
5. 響應式設計正常
