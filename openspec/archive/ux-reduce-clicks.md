---
title: UX 減少點擊優化
type: refactor
status: completed
created: 2026-02-16
---

# UX 減少點擊優化

## 變更內容

基於前端 UX 分析，針對「減少點擊次數」進行三項高影響優化：

### 1. 合併「本年」和「流年」tab（FortuneTab）

現狀：本年(Yearly)和流年(Decade)是獨立的 sub-tab，資訊重疊
- 本年：單年九曜星資訊 + 各項運勢
- 流年：十年趨勢圖 + 可展開按年

修正：合併為單一「流年」tab，預設顯示當年詳情 + 十年趨勢
- 節省 1 次點擊，5 個 sub-tab → 4 個
- 減少資訊重複

### 2. 配對清單加「快速查看相性」（MatchTab）

現狀：查看已存配對的相性需要切到「相性診斷」tab 重新輸入日期
修正：在「我的配對」清單中直接顯示相性摘要（關係類型 + 分數）
- 節省 2 次點擊

### 3. SummaryCard 點擊展開今日詳細運勢

現狀：SummaryCard 只顯示分數，查詳情要切到 Fortune tab
修正：點擊 SummaryCard 自動切到 Fortune Daily tab
- 節省 1 次點擊

## 影響範圍

- `frontend/src/components/FortuneTab.vue` — 合併 Yearly/Decade
- `frontend/src/components/MatchTab.vue` — Partners 快速相性
- `frontend/src/components/SummaryCard.vue` — 點擊導航
- `frontend/src/views/HomeView.vue` — tab 切換事件

## UI/UX 規格

| 項目 | 規格 |
|------|------|
| 色彩 | 沿用現有 PrimeVue Aura 主題變數 |
| 間距 | 4px 基數（8/12/16/24px） |
| 元件 | PrimeVue TabView, Card, Tag |
| 響應式 | 維持現有 RWD 斷點 |
| 互動 | SummaryCard 加 cursor:pointer + hover 效果 |
| 無障礙 | Tab 切換保持 ARIA role |

## 測試計畫

1. FortuneTab：合併後 Yearly 內容完整，Decade 趨勢圖正常
2. MatchTab：Partners 清單顯示相性摘要，點擊展開詳情
3. SummaryCard：點擊後正確切到 Fortune Daily
4. 行動裝置：sub-tab 減少後不需水平捲動

## Checklist

- [x] FortuneTab 合併 Yearly/Decade
- [x] MatchTab Partners 方向/元素資訊
- [x] SummaryCard 點擊導航
- [x] HomeView tab 切換連動
- [x] TypeScript 型別檢查通過
- [x] Vite 建構成功
