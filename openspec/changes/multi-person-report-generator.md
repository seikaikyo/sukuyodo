---
title: 多人關係分析報告產生器
type: feature
status: completed
created: 2026-02-20
---

# 多人關係分析報告產生器

## 變更內容

將目前手動分析的流程系統化，提供一個介面讓用戶輸入多位人物（含公司/組織），自動產生完整的宿曜道關係分析報告（HTML），包含：

1. 閱讀指南（術語詞彙表）
2. 人物檔案（本命宿/元素/角色/元素互動分析）
3. 全員相性矩陣（含方向性、分數）
4. 九曜流年總覽（多人折線圖 + 對照表）
5. 月度分數明細（含凌犯月標記）
6. 關鍵日期運勢分析（含暗黒/甘露/金剛峯/羅刹日標注）
7. 勢力結構分析（自動分群：支持者/威脅/中性）
8. 模式分析（交替互補/同時高運/同時低運）
9. 結語

## 實作方案：純前端生成（後端零修改）

延續現有三份報告的模式，前端利用現有 API 平行呼叫收集數據，在 `report-generator.ts` 新增 `generateMultiPersonReport()` 組裝 HTML 下載。

## 影響範圍

| 檔案 | 修改內容 |
|------|---------|
| `frontend/src/utils/report-generator.ts` | 新增 `generateMultiPersonReport()` + 分析引擎 + 多人 CSS |
| `frontend/src/components/ReportTab.vue` | 新增報告輸入表單 |
| `frontend/src/composables/useSukuyodo.ts` | activeMainTab 加入 'report' |
| `frontend/src/views/HomeView.vue` | 新增 ReportTab 入口 + 報告 tab |

## 測試計畫

1. TypeScript 型別檢查通過
2. Vite 建構通過
3. 用兩人產生精簡報告，確認基本功能
4. 用六人產生完整報告，與手動版 report_complete_analysis.html 對比
5. 測試事件分析功能
6. 測試匯入收藏功能

## Checklist

- [x] report-generator.ts 多人報告函數
- [x] ReportTab.vue 報告表單介面
- [x] HomeView.vue 入口整合
- [x] TypeScript 型別檢查通過
- [x] Vite 建構通過
