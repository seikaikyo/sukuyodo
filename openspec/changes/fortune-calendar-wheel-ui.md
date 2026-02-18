---
title: 吉凶月曆與宿曜輪盤互動 UI
type: feature
status: completed
created: 2026-02-18
---

# 吉凶月曆與宿曜輪盤互動 UI

## 背景

參考八雲院（yakumoin.net）的宿曜占星盤和凌犯期間吉凶日曆，為 sukuyodo 新增兩個視覺化功能：

1. **吉凶月曆**：月曆格式顯示凌犯期間、甘露/金剛峯/羅刹日、個人三期サイクル
2. **宿曜輪盤升級**：現有 MansionWheel.vue 升級為可互動、支援多模式的占星盤

## 參考來源

- yakumoin.net/about/senseiban（輪盤：可旋轉，雙模式）
- yakumoin.net/about/ryouhan_kikkyou_list（月曆：灰色凌犯背景，甘/金/羅標記）
- sukuyou.divination.page/2026-calendar（月曆：旧暦對應）

## 功能需求

### A. 吉凶月曆

#### 公開層（不需要生日）
- 標準週制表格（日月火水木金土）
- 每日顯示：當日宿名、七曜
- 凌犯期間：灰色背景標示
- 甘露日/金剛峯日/羅刹日：「甘」「金」「羅」標籤 + 色彩
- 日本選日：天赦日、一粒萬倍日等
- 年/月切換導覽
- 月份統計（凌犯天數、甘露/金剛峯/羅刹日數）

#### 個人化層（輸入生日後疊加）
- 三期サイクル色帶（躍動/破壊/再生）
- 暗黒の一週間標記
- 六害宿標記（僅凌犯期間）
- 每日運勢分數（圓點或色塊）
- 宿曜關係類型（命/栄/衰/安/危/成/壊/友/親/業/胎）
- 多因素交叉分析警示

### B. 宿曜輪盤升級

#### 現有 MansionWheel.vue 升級
- 觸控/拖曳旋轉
- 五行元素色彩環
- 雙模式：
  - 相性模式：點擊宿位顯示三九秘法關係
  - 運勢模式：當日宿高亮 + 今日關係
- 六害宿標記（凌犯期間）
- 三期サイクル弧形色帶

## 影響範圍

### 後端
- `backend/services/sukuyodo.py` - 新增統合月曆 API 方法
- `backend/routers/sukuyodo.py` - 新增端點

### 前端
- `frontend/src/components/MansionWheel.vue` - 升級輪盤
- `frontend/src/components/FortuneCalendar.vue` - 新元件：吉凶月曆
- `frontend/src/composables/useSukuyodo.ts` - 新增 API 方法
- `frontend/src/views/HomeView.vue` - 整合新分頁/元件
- `frontend/src/styles/variables.css` - 可能新增色彩變數

## UI/UX 規格

### 色彩
| 用途 | 色彩 | 變數名 |
|------|------|--------|
| 凌犯背景 | rgba(255,100,100,0.15) | --ryouhan-bg |
| 甘露日 | #4CAF50 (綠) | --kanro-color |
| 金剛峯日 | #D4AF37 (金) | --kongou-color |
| 羅刹日 | #E53935 (紅) | --rasetsu-color |
| 躍動の週 | rgba(76,175,80,0.1) | --sanki-active-bg |
| 破壊の週 | rgba(229,57,53,0.1) | --sanki-destroy-bg |
| 再生の週 | rgba(33,150,243,0.1) | --sanki-rebirth-bg |
| 暗黒の一週間 | rgba(0,0,0,0.3) | --dark-week-bg |

### 間距
- 月曆格子：最小 40x40px（mobile）、60x60px（desktop）
- 格子內間距：4px
- 月份標題：margin-bottom 16px

### 響應式
- Mobile (<768px)：月曆格子壓縮，輪盤縮至 280px
- Tablet (<1024px)：月曆全寬，輪盤 360px
- Desktop (>=1024px)：月曆+輪盤並排或分頁

## 後端 API 設計

### 新端點：GET /api/sukuyodo/calendar/monthly/{year}/{month}

不需要生日，回傳整月的公開吉凶資訊：

```json
{
  "year": 2026,
  "month": 2,
  "days": [
    {
      "date": "2026-02-01",
      "weekday": "日",
      "day_mansion": { "name_jp": "...", "index": 0, "element": "木" },
      "special_day": null | { "type": "kanro", "name": "甘露日" },
      "ryouhan": null | { "active": true, "lunar_month": 1 },
      "japanese_calendar": { "types": [...], "labels": [...] }
    }
  ],
  "ryouhan_periods": [...],
  "statistics": {
    "ryouhan_days": 0,
    "kanro_count": 1,
    "kongou_count": 1,
    "rasetsu_count": 1,
    "tensya_count": 0,
    "ichiryumanbai_count": 3
  }
}
```

### 新端點：GET /api/sukuyodo/calendar/monthly/{year}/{month}?birth_date=YYYY-MM-DD

加入生日參數後，疊加個人化資訊：

```json
{
  "...公開資訊...",
  "personal": {
    "your_mansion": { "name_jp": "觜宿", "index": 18 },
    "days": [
      {
        "date": "2026-02-01",
        "relation_type": "ankai",
        "relation_name": "安壊",
        "fortune_score": 45,
        "sanki_period": "破壊の週",
        "is_dark_week": true,
        "rokugai": null | { "name": "命宿" },
        "compound_analysis": [...]
      }
    ]
  }
}
```

## 測試計畫

1. 公開月曆：對比 yakumoin.net 2026 年凌犯期間和特殊日
2. 個人月曆：對比 /fortune/daily API 回傳的個別日期資料
3. 輪盤：驗證 27 宿排列、旋轉功能、關係標示
4. 響應式：手機/平板/桌面三個斷點測試
5. 效能：月曆載入 < 500ms

## Checklist
- [x] 後端：統合月曆 API
- [x] 前端：FortuneCalendar 元件（公開層）
- [x] 前端：FortuneCalendar 個人化層
- [x] 前端：MansionWheel 升級
- [x] 整合至 HomeView
- [ ] 響應式測試
- [ ] 交叉驗證
