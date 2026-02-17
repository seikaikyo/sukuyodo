---
title: 驗證後前端清理
type: refactor
status: completed
created: 2026-02-17
---

# 驗證後前端清理

## 變更內容
完整驗證宿曜經計算系統後，發現 3 個前端問題需要修正：
1. MatchTab.vue 的 `/profile` 連結指向不存在的路由（app 只有 `/` 路由）
2. useSukuyodo.ts 存在大量死碼（7 個未使用的 export、1 個 init 中的無效呼叫）
3. 後端 `/career-guidance` 端點無前端呼叫者（暫不處理，僅記錄）

## 影響範圍
- `frontend/src/components/MatchTab.vue` — 修正壞掉的連結
- `frontend/src/composables/useSukuyodo.ts` — 移除死碼

## 測試計畫
1. 確認 MatchTab 空狀態顯示正確，點擊可導航
2. 確認移除死碼後前端正常運作（吉日功能不受影響）
3. 確認 TypeScript 編譯無錯誤

## Checklist
- [x] 修正 MatchTab.vue `/profile` 連結
- [x] 移除 useSukuyodo.ts 死碼
- [x] 驗證前端正常運作
