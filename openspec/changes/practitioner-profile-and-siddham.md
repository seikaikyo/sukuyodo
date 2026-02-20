---
title: 修行背景檔案與悉曇真言發音指南
type: feature
status: completed
created: 2026-02-20
---

# 修行背景檔案與悉曇真言發音指南

## 變更內容

### 1. Profile Store 新增修行背景欄位
- `practitionerLevel: 'none' | 'tokudo' | 'ajari'` — 預設 'none'
- `isPractitioner` computed：practitionerLevel !== 'none'
- 舊資料遷移：無 practitionerLevel 欄位時預設 'none'

### 2. HomeView Profile Panel 修行背景選擇
- 三個按鈕：一般 / 得度 / 阿闍梨（使用 Shoelace 風格，與現有 UI 一致）
- 位置：「我的生日」區段後、「收藏對象」區段前

### 3. FortuneTab 根據 Profile 自動切換
- 從 profile store 讀取 isPractitioner
- isPractitioner 為 true 時，decadePerspective 初始值為 'practitioner'
- watcher 監聽 profile 變更自動同步
- 保留手動切換按鈕

### 4. 後端 mantra 新增悉曇欄位
- siddham_bija：種子字日文讀音
- siddham_roman：IAST 羅馬轉寫
- siddham_unicode：悉曇 Unicode 碼點

### 5. 悉曇字體載入
- NotoSansSiddham-Regular.woff2（84KB）自行託管
- index.html @font-face 宣告

### 6. 前端真言區塊改版
- 新增 mantra-bija-section：悉曇種子字 2.5rem + IAST + 本尊名
- 原有真言文字移至 mantra-text-section

### 7. 報告生成器更新
- buildYearCardPractitioner mantra-box 加入 IAST + 種子字讀音
- 報告不嵌入悉曇 Unicode（列印穩定性考量）

## 影響範圍
- `frontend/src/stores/profile.ts`
- `frontend/src/views/HomeView.vue`
- `frontend/src/components/FortuneTab.vue`
- `frontend/src/utils/report-generator.ts`
- `frontend/index.html`
- `frontend/public/fonts/NotoSansSiddham-Regular.woff2`（新增）
- `backend/services/sukuyodo.py`

## 驗證結果
- [x] TypeScript 型別檢查通過
- [x] Vite 建構成功
- [x] API 回應含 siddham_bija / siddham_roman / siddham_unicode
- [x] 九曜 Unicode 碼點逐一對照 unicodedata.name() 驗證
- [x] Profile Store 遷移邏輯正確
