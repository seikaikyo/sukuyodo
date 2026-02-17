---
title: 六害宿修正 + 暗黒の一週間 + 凌犯全面逆轉 + UX 改善
type: fix
status: completed
created: 2026-02-16
---

# 六害宿修正 + 宿曜經規則補完 + UX 改善

## 背景

全面交叉驗證發現 1 個 Bug 和 2 個遺漏規則：

1. **六害宿偏移量錯誤**：三個外部來源（yakumoin.net, kosei-do.co.jp, sukuyou.divination.page）確認正確偏移為 0,3,9,12,15,19（加法），現行系統為 0,2,8,11,14,18（減法）
2. **暗黒の一週間未標注**：破壊の週中 distance 9-15 的 7 天是最凶期間，多數宿曜網站都有標注
3. **凌犯期間僅逆轉特殊日**：完整規則是凌犯期間中吉日（栄/安/成等）也會受影響

另外 UX 有 3 個需改善項目。

## 變更內容

### 1. 六害宿偏移量修正（Bug Fix）

修改 ROKUGAI_OFFSETS：
- 0 → 0（命宿，不變）
- 2 → 3（意宿 = 一九の安）
- 8 → 9（事宿 = 業）
- 11 → 12（克宿 = 二九の安）
- 14 → 15（聚宿 = 二九の壊）
- 18 → 19（同宿 = 三九の栄）

修改計算方向：`(birth - offset) % 27` → `(birth + offset) % 27`

### 2. 暗黒の一週間標記

三期サイクル回傳中新增 `is_dark_week` flag。
- 條件：破壊の週 + distance 9-15
- 前端顯示小提示

### 3. 凌犯期間吉凶影響

凌犯期間中，非特殊日的吉日（栄/安/成/友/親）也受輕微負面影響。
- 日運分數在凌犯期間中額外 -3（吉日型）或 +3（凶日型：衰/壊/危）
- 不影響特殊日（甘露/金剛峯/羅刹的逆轉已處理）

### 4. UX 改善

- 觸控目標：所有 pill-btn 和 nav-btn 加 min-height: 44px
- 知識 tab：進階主題（凌犯/三期/傍通曆）合併為「進階」一個 tab
- 月運勢：expandedMonthlyWeek 預設為 currentWeekNumber

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `backend/services/sukuyodo.py` | ROKUGAI_OFFSETS 修正、暗黒の一週間 flag、凌犯期間分數調整 |
| `frontend/src/components/FortuneTab.vue` | 暗黒の一週間提示、觸控目標、月運預設展開 |
| `frontend/src/components/KnowledgeTab.vue` | 合併進階 tab、觸控目標 |
| `frontend/src/components/LuckyDaysTab.vue` | 觸控目標 |
| `frontend/src/components/MatchTab.vue` | 觸控目標 |
| `frontend/src/views/HomeView.vue` | 觸控目標 |
| `frontend/src/composables/useSukuyodo.ts` | DailyFortune.sanki 型別更新 |

## 測試計畫

1. 六害宿：用觜宿(18)計算，確認 6 個位置為 觜(18)/鬼(21)/角(0)/房(3)/箕(6)/危(10)
2. 暗黒の一週間：觜宿 distance 9-15 時 is_dark_week=true
3. 凌犯期間調整：2026/6 月凌犯期間中的吉日分數有微調
4. 觸控目標：行動裝置測試按鈕大小
