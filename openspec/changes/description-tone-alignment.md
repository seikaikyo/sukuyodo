---
title: 描述文字語氣校準：對齊原典引導精神
type: fix
status: completed
created: 2026-02-24
---

# 描述文字語氣校準：對齊原典引導精神

## 變更內容

全面校準系統中描述文字的語氣，確保每段描述都遵循原典「面對、接受、解法」三層結構：
1. 面對：坦白告知能量狀態（不粉飾不恐嚇）
2. 接受：說明這是循環的一部分（去除宿命感）
3. 解法：提供具體可做的事（賦予行動力）

修正對象：
- P1 級 6 處：kyo 描述宿命感/否定感、安壊絕對化、前端負面用語
- P2 級 5 處：用詞過重、語氣不夠典雅、歸因方式修正

## 影響範圍
- `backend/services/sukuyodo.py` — 年度 kyo 描述微調、安壊/九曜星描述修正
- `frontend/src/components/MatchTab.vue` — 危方/壊方建議文字、「避開」措辭
- `frontend/src/utils/ics-generator.ts` — 凌犯逆轉 iCal 描述

## 測試計畫
1. curl 測試 2027 年（火曜星大凶）描述是否符合三層結構
2. curl 測試安壊相性描述
3. 前端文字確認無恐嚇語氣

## Checklist
- [x] 後端 kyo 描述 5 處修正（advice/career/love/health/wealth）
- [x] 後端安壊 detailed 修正（「走向破裂」→「推動成長的力量」）
- [x] 後端九曜星（火曜/計都）世俗描述修正
- [x] 前端 MatchTab 危方/壊方修正（「破壞性衝突」→「打破現狀推動改變」）
- [x] 前端 MatchTab 「避開」→「建議謹慎（需特別準備）」
- [x] 前端 ics-generator 凌犯描述 3 處修正
- [x] API 端對端驗證（12 項全 PASS）
