---
title: 全面內容加強 - 運勢描述、宿曜知識、關係說明
type: feature
status: in-progress
created: 2026-02-14
---

# 全面內容加強

## 變更內容

使用者反映系統內容偏少，需要更詳細、更直白的說明。涵蓋以下範圍：

### 1. 二十七宿描述加強 (sukuyodo_mansions.json)
- personality: 目前平均 100 字 → 目標 200+ 字
- love: 目前平均 80 字 → 目標 150+ 字
- career: 目前平均 72 字 → 目標 150+ 字
- health: 目前平均 68 字 → 目標 150+ 字

### 2. 六種關係描述加強 (sukuyodo_mansions.json)
- description: 目前平均 71 字 → 目標 120+ 字
- detailed: 目前平均 191 字 → 目標 300+ 字
- advice: 目前平均 50 字 → 目標 100+ 字
- tips: 目前 3 條 → 目標 5 條
- avoid: 目前 2-3 條 → 目標 5 條

### 3. 運勢描述擴充 (sukuyodo.py)
- DAILY_FORTUNE_DESCRIPTIONS: 目前每類 1 條 → 目標每類 3-5 條
- MONTHLY_FORTUNE_DESCRIPTIONS: 目前每類 1 條 → 目標每類 3-5 條
- daily_advice (sukuyodo_fortune.json): 目前每級 3 條 (37 字) → 目標每級 5 條 (60+ 字)

### 4. 知識頁籤加強 (KnowledgeTab.vue + sukuyodo_mansions.json)
- 七曜: 只有 planet/traits/energy → 加入完整說明、象徵意義、對應關係
- 傍通曆: 只有 2 列範例 → 完整 12 個月對照表 + 使用說明
- 歷史: 只有 4 行 metadata → 完整歷史敘述（起源、傳入日本、發展、現代應用）

## 影響範圍
- `backend/data/sukuyodo_mansions.json` - 宿描述、關係描述、七曜資料、歷史 metadata
- `backend/data/sukuyodo_fortune.json` - daily_advice 擴充
- `backend/services/sukuyodo.py` - DAILY/MONTHLY_FORTUNE_DESCRIPTIONS 擴充
- `frontend/src/components/KnowledgeTab.vue` - 知識頁籤 UI 適配新內容

## 測試計畫
1. 後端 API 回傳新內容完整性驗證
2. 前端頁面載入無錯誤
3. agent-browser 截圖確認排版正常
4. 內容長度統計確認達標

## Checklist
- [ ] 二十七宿描述加強
- [ ] 六種關係描述加強
- [ ] 運勢描述擴充
- [ ] daily_advice 擴充
- [ ] 七曜知識加強
- [ ] 傍通曆完整化
- [ ] 歷史內容加強
- [ ] 知識頁籤 UI 適配
- [ ] 測試驗證
