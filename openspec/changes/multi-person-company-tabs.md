---
title: 多人公司速查頁籤
type: feature
status: completed
created: 2026-02-23
---

# 多人公司速查頁籤

## 變更內容

在配對 > 公司速查區域新增「求職者頁籤」，讓不同人各自擁有獨立的公司清單和批次分析結果。

目前系統是單一使用者 profile，只有一份公司清單。改成支援多位求職者，各自有 birthDate + companies[]，用頁籤切換。

### 需求場景
- Dash 有自己的公司清單（已存在於 companies.json）
- 正念 (1991/01/27) 有另一組適合她的公司清單
- 兩人的 birthDate 不同，同一家公司的相性/梯隊完全不同
- 用頁籤在同一個介面快速切換

## 影響範圍

| 檔案 | 變更 |
|------|------|
| `frontend/src/stores/profile.ts` | 新增 `JobSeeker` 介面和相關 CRUD |
| `frontend/src/components/MatchTab.vue` | 公司速查區加求職者頁籤 |
| `frontend/src/views/HomeView.vue` | 支援 per-seeker 的 batch analysis |
| `frontend/src/composables/useSukuyodo.ts` | batch analysis 支援傳入不同 birthDate |
| `frontend/public/companies-zhennian.json` | 正念的推薦公司清單（新檔案） |

## 技術設計

### 1. 資料結構 (profile.ts)

```typescript
export interface JobSeeker {
  id: string
  name: string
  birthDate: string  // YYYY-MM-DD
  companies: Company[]
  companiesJsonFile?: string  // 對應的 JSON 檔名
}
```

在 UserProfile 中新增：
```typescript
jobSeekers: JobSeeker[]  // 額外的求職者（自己不在這裡，用原本的 birthDate + companies）
```

### 2. UI 結構 (MatchTab.vue)

在公司速查區頂部加求職者頁籤：
```
┌─────┬──────┬────────┐
│ Dash │ 正念 │ + 新增  │
└─────┴──────┴────────┘
```
- 點 Dash → 顯示 profile.birthDate + profile.companies 的 batch result
- 點 正念 → 顯示正念的 birthDate + 正念的 companies 的 batch result
- 每個頁籤獨立管理公司清單（新增/移除/匯入）

### 3. 批次分析邏輯

- 各求職者的 batch result 獨立存放（Map<seekerId, CompanyBatchResult>）
- 切換頁籤時，如果該求職者還沒跑過分析，自動觸發
- 公司清單變動時重新計算

### 4. 正念的推薦清單 (companies-zhennian.json)

從剛才分析的 20 家台南公司中，挑出前兩梯隊 + 有潛力的第四梯隊，預設匯入。

## UI/UX 規格

- 頁籤樣式：與現有 main-tabs 一致的 pill style
- 間距：8px gap between tabs
- 新增求職者：點「+」彈出 Dialog，輸入名稱 + 生日
- 刪除求職者：長按或右滑顯示刪除（或 card 上的 x 按鈕）
- 顏色：頁籤不需要額外顏色，active 用現有 accent

## 測試計畫

1. Dash 頁籤顯示原有公司清單和 batch result
2. 新增正念 → 輸入 1991-01-27 → 匯入推薦清單 → 自動跑 batch analysis
3. 切換頁籤，兩人的結果各自獨立
4. 重新整理頁面，兩人的資料都保留（localStorage）
5. 刪除求職者，對應的公司清單一併移除

## Checklist

- [x] profile.ts 新增 JobSeeker 結構
- [x] MatchTab.vue 公司速查區加頁籤
- [x] HomeView.vue 支援 per-seeker batch analysis
- [x] useSukuyodo.ts 支援不同 birthDate
- [x] companies-zhennian.json 正念的推薦公司清單
- [x] localStorage 存取正確
- [x] 頁籤切換流暢
- [x] TypeScript 型別檢查通過
- [x] Vite build 通過
