---
title: UI 修正 - 背景/趨勢/特殊日標記/知識典據
type: fix
status: completed
created: 2026-02-20
---

# UI 修正 - 背景/趨勢/特殊日標記/知識典據

## 變更內容

### 1. 背景減輕
- variables.css 基底色整體提亮 1-2 級（保持星空風格但不壓迫）
- HomeView.vue `--bg-primary` 同步調整

### 2. 月度趨勢圖縮小
- FortuneTab.vue SVG 尺寸/高度減少

### 3. 各月運勢卡片恢復特殊日標記
- 後端 monthly_trend 加入 `special_day_counts`（每月甘露/金剛峯/羅刹日數量）
- 前端 monthly-card 分數旁顯示三色標記（甘/金/羅）

### 4. 知識 - 凌犯期間加入漢文原典與日文
- sukuyodo_mansions.json ryouhan_knowledge sections 加入 content_classic + content_ja
- KnowledgeTab.vue ryouhan 區塊渲染 classic-quote + ja-text

### 5. 知識 - 傍通曆加入原典出處
- sukuyodo_mansions.json 或 KnowledgeTab.vue calendar 區塊加入出處說明

## 影響範圍
- `frontend/src/styles/variables.css`
- `frontend/src/views/HomeView.vue`
- `frontend/src/components/FortuneTab.vue`
- `frontend/src/components/KnowledgeTab.vue`
- `backend/services/sukuyodo.py`
- `backend/data/sukuyodo_mansions.json`

## 驗證計畫
- [x] 背景視覺減輕（基底色 +1-2 級）
- [x] 趨勢圖尺寸縮小（620x200 → 560x160）
- [x] 各月卡片顯示特殊日標記（甘/金/羅 + 日數）
- [x] 凌犯知識四節全加漢文原典 + 日文
- [x] 傍通曆有原典出處（品第四）
- [x] TypeScript 無錯誤
- [x] Vite 建構通過
- [x] 後端 monthly_trend special_day_counts 12 個月驗證通過
