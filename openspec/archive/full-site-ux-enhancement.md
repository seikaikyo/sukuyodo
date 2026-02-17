---
title: 全站易讀性與色彩統一優化
type: feature
status: completed
created: 2026-02-16
---

# 全站易讀性與色彩統一優化

## 背景

使用者反映「跟你問過才發現很多功能都沒講清楚」、「顏色要統一，運勢裡面有些綠色是大吉比金色好？有些卻是反過來？」。三個審查 agent 共找出約 82 個問題，本次聚焦在影響最大的項目。

## 變更內容

### 1. 色彩系統統一（使用者明確要求）

**問題**: HomeView.vue 的 `--success: #22c55e`(綠) 用於 excellent(90+)，`--accent: #f59e0b`(金) 用於 good(75+)。但宿曜以金色為最高等級（星光金），綠色反而排第二，造成混淆。

**修正**: 重新定義語意色彩，金色=最高，綠色=次高：

| 等級 | 分數 | 修正前 | 修正後 |
|------|------|--------|--------|
| excellent | 90+ | --success(綠) | --stellar(金) #d4a017 |
| good | 75+ | --accent(琥珀) | --success(綠) #4a9b6b |
| fair | 60+ | --info(藍) | --info(藍) 不變 |
| caution | 45+ | #eab308 | #eab308 不變 |
| warning | <45 | --warning(紅) | --warning(紅) 不變 |

影響：FortuneTab、LuckyDaysTab、MatchTab 中所有 score-fill、score-value、daily-item、hint-relation 等 CSS class。

### 2. 日文翻譯為中文

**2a. 三期日型描述 (SANKI_DAY_TYPES)**
backend 的 SANKI_DAY_TYPES 全部是日文描述，翻譯為正體中文。

**2b. 凌犯訊息**
- FortuneTab.vue L142: `凌犯期間中のため吉凶が逆轉しています` → `凌犯期間，吉凶逆轉`
- LuckyDaysTab.vue L300: 同上

**2c. 暗黑週標籤**
- FortuneTab.vue L160: `暗黒の一週間` → `暗黑週`（保留專有名詞感但用中文字）

### 3. 分數等級圖例

在 FortuneTab 的分數條旁新增迷你圖例，說明分數區間意義：
- 90+: 大吉（金）
- 75+: 吉（綠）
- 60+: 中吉（藍）
- 45+: 小吉（黃）
- <45: 注意（紅）

### 4. 關係提示標籤顏色統一

FortuneTab 的 `.hint-relation` 色彩使用與分數相同的統一色系：
- eishin(栄親) = 大吉 → 金色
- gyotai(業胎) = 吉 → 綠色
- mei(命) = 中吉 → 藍色
- yusui(友衰) = 中等 → 次色
- kisei(危成) = 小吉 → 黃色
- ankai(安壊) = 注意 → 紅色

### 5. 知識 tab 子分頁名稱改善

| 原名 | 修正 | 原因 |
|------|------|------|
| 七曜 | 五行七曜 | 「七曜」容易和星期搞混 |
| 凌犯 | 凌犯逆轉 | 更明確 |
| 三期 | 三九秘曆 | 傳統稱呼，更有辨識度 |

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `frontend/src/views/HomeView.vue` | CSS 變數重新定義 |
| `frontend/src/components/FortuneTab.vue` | 分數色彩 class、凌犯中文、暗黑週、分數圖例、關係提示色 |
| `frontend/src/components/LuckyDaysTab.vue` | 分數色彩 class、凌犯中文 |
| `frontend/src/components/MatchTab.vue` | 分數色彩 class |
| `frontend/src/components/KnowledgeTab.vue` | 子分頁名稱 |
| `backend/services/sukuyodo.py` | SANKI_DAY_TYPES 中文翻譯 |

## 測試計畫

1. pm2 restart 前後端
2. curl API 確認三期描述回傳中文
3. 瀏覽器確認各 tab 色彩統一：金色=最高、綠色=次高
4. 確認凌犯訊息顯示中文
5. 確認知識 tab 子分頁名稱已更新
