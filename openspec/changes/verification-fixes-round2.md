---
title: 驗證第二輪修正
type: fix
status: completed
created: 2026-02-17
---

# 驗證第二輪修正

## 變更內容
完整交叉驗證（120 項全部通過）後，發現以下問題：

1. **report-generator.ts L812-813 API 參數名稱錯誤** — `?date=` 應為 `?birth_date=`，導致雙人流年報告匯出失敗（422 Unprocessable Entity）
2. **useSukuyodo.ts 殘餘死碼** — `luckyDayResult`/`luckyDayLoading` ref 在上次清理移除 `fetchLuckyDays()` 後已無寫入者，也無元件讀取
3. **MEMORY.md index 記載錯誤** — 觜宿記為 index=19（正確 18）、井宿記為 index=21（正確 20）

## 影響範圍
- `frontend/src/utils/report-generator.ts` — 修正 API 參數名稱
- `frontend/src/composables/useSukuyodo.ts` — 移除殘餘死碼
- `.claude/projects/.../memory/MEMORY.md` — 修正 index 記載

## 測試計畫
1. 確認 TypeScript 編譯無錯誤
2. 確認 yearly-range API 參數正確

## Checklist
- [x] 修正 report-generator.ts API 參數
- [x] 移除 useSukuyodo.ts 殘餘死碼
- [x] 更新 MEMORY.md
- [x] 驗證前端編譯
