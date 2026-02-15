---
title: 內容增強第二階段 - 前端展示完善與動態內容擴充
type: feature
status: completed
created: 2026-02-15
---

# 內容增強第二階段

## 背景

第一階段已將後端靜態內容從 ~32,000 字擴充至 ~61,700 字，27 宿描述和距離化相性
描述已達專業級。但前端展示層仍有數處內容不足，動態生成的運勢描述也偏短。

## 變更內容

### P0: 我的配對（Partners Tab）完整化

**問題**: 只顯示姓名、宿名、關係名、分數，零敘述內容
**修改**: 擴充 partner 卡片，加入完整相性資訊

- 顯示關係描述（description）
- 顯示距離分類標籤（近/中/遠距離）
- 顯示建議摘要（advice 截斷前 100 字）
- 顯示愛情/事業面向（love/career）
- 點擊可展開完整相性分析（複用相性診斷的顯示邏輯）

**檔案**: `frontend/src/components/MatchTab.vue`
**後端**: `frontend/src/composables/useSukuyodo.ts`（PartnerCompatibility 型別擴充）

### P0: 月運/年運建議文字擴充

**問題**: 月運 theme 只有標題 + 1 句 focus，年運建議只有 ~40 字
**修改**:
- 月運: 加入 `theme.description`（月度趨勢分析 200-300 字）
- 年運: advice 從 ~40 字擴充至 ~150 字，加入各月份簡評
- 後端 MONTHLY/YEARLY 生成邏輯增加描述文字

**檔案**: `backend/services/sukuyodo.py`（月/年運勢生成函數）

### P1: 運勢頁建議文字加深

**問題**: 每日/每週建議只有 1 段 100-150 字
**修改**:
- 加入「今日宿曜提示」欄位，解釋當日值宿與本命宿的關係含義
- 週運加入「本週焦點」段落（100 字）
- 利用既有的 mansion_relation 資料生成解說

**檔案**: `backend/services/sukuyodo.py`（每日/每週運勢生成）
**檔案**: `frontend/src/components/FortuneTab.vue`（顯示新欄位）

### P1: 吉日解說擴充

**問題**: 只有日期列表，缺少「為什麼這天吉」的解說
**修改**:
- 吉日結果加入 `reason_detail`（每個吉日 50-80 字說明）
- 選日曆注 legend 擴充（每項 100-150 字）
- 配對吉日加入互動建議

**檔案**: `backend/services/sukuyodo.py`（吉日生成邏輯）
**檔案**: `frontend/src/components/LuckyDaysTab.vue`（顯示擴充描述）

### P2: 配對尋找配對說明擴充

**問題**: 各關係類型描述只有 50-100 字
**修改**:
- 尋找配對各關係分類加入 `detailed` 長描述（200-300 字）
- 已儲存的 partner 在尋找配對中高亮標記

**檔案**: `frontend/src/components/MatchTab.vue`（尋找配對區段）

## 影響範圍

- `backend/services/sukuyodo.py` - 動態描述生成擴充
- `frontend/src/components/MatchTab.vue` - Partners 完整化 + Finder 擴充
- `frontend/src/components/FortuneTab.vue` - 新欄位顯示
- `frontend/src/components/LuckyDaysTab.vue` - 吉日說明
- `frontend/src/composables/useSukuyodo.ts` - 型別擴充

## 不做的事

- 不改計算邏輯（已驗證正確）
- 不新增 API 端點（擴充現有回傳欄位）
- 不改後端靜態資料檔（第一階段已充分擴充）

## 測試計畫

1. curl 測試各 API 回傳新增欄位
2. 瀏覽器驗證我的配對顯示完整資訊
3. 確認月運/年運建議文字長度達標
4. 吉日頁面顯示說明文字

## Checklist

- [x] Partners Tab 完整化（展開式卡片，完整相性資訊）
- [x] 月運/年運建議擴充（YEARLY_FORTUNE_ADVICE + MONTHLY_THEME_DESCRIPTIONS）
- [ ] 每日/週運建議加深（P1 下一階段）
- [x] 吉日解說擴充（reason 從 ~30 字擴充至 ~80 字）
- [x] 尋找配對說明擴充（detailed 描述 + 展開按鈕）
- [x] Bug: dialog @sl-after-hide（已在 HomeView.vue 修正）
- [x] Bug: quickSelect 不覆蓋 profile（已在 HomeView.vue 修正）
- [x] Bug: finder year_range 中心年（已在 sukuyodo.py 修正）
