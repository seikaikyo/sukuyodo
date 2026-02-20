---
title: UI/UX 全面優化（無障礙、一致性、響應式、微互動）
type: refactor
status: in-progress
created: 2026-02-20
---

# UI/UX 全面優化

## 變更內容

基於專業 UI 審查，修正四大類問題：

### A. 無障礙 + 對比度修正
- `--text-muted` (#A09890) 未達 WCAG AA → 加深至 #7A7570
- 缺少 focus-visible 的元素補齊
- 按鈕 touch target 統一 44px（修正 width:32px + min-height:44px 的矛盾）
- 補齊缺少的 aria 屬性

### B. 元件一致性
- `.pill-btn` 重複定義於 FortuneTab / MatchTab / KnowledgeTab → 抽至 global.css
- `.excellent/.good/.fair/.caution/.warning` 色彩 class → 抽至 global.css
- 按鈕尺寸統一（icon btn 44x44）
- 間距統一使用 4px 倍數

### C. 響應式優化
- 新增 tablet 斷點 (1024px)
- 月曆格子手機版可讀性（字體放大、格子加寬）
- SVG 圖表改為 viewBox 自適應
- Partner list 手機版排版

### D. 微互動 + 過渡
- 統一 transition 使用 CSS 變數
- 卡片 hover 效果統一
- 分數條動畫時間統一

## 影響範圍
- `frontend/src/styles/variables.css` — 修正 text-muted 對比度
- `frontend/src/styles/global.css` — 新增共用 utility class
- `frontend/src/views/HomeView.vue` — 按鈕尺寸、間距修正
- `frontend/src/components/FortuneTab.vue` — pill-btn 改用 global、過渡統一
- `frontend/src/components/MatchTab.vue` — 同上
- `frontend/src/components/KnowledgeTab.vue` — 同上
- `frontend/src/components/LuckyDaysTab.vue` — caution 色 class
- `frontend/src/components/FortuneCalendar.vue` — 響應式格子
- `frontend/src/components/SummaryCard.vue` — hover 效果
- `frontend/src/components/MansionWheel.vue` — SVG viewBox

## 測試計畫
1. Vite build 無錯誤
2. 各 Tab 頁面視覺確認
3. 手機寬度 (375px) 月曆/圖表可讀
4. 鍵盤 Tab 導航測試 focus-visible
