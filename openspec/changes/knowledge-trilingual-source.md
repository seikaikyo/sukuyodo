---
title: 知識庫三語說明與原典出處補齊
type: fix
status: completed
created: 2026-02-20
---

# 知識庫三語說明與原典出處補齊

## 變更內容

1. 月宿傍通曆（key_concepts）補齊 content_classic、content_ja，加入原典出處
2. 三九秘法、二十七宿與二十八宿（key_concepts）同步補齊三語+出處
3. 凌犯期間（ryouhan_knowledge）加入明確 CBETA 出處引用
4. 前端 key_concepts 模板補上 content_classic / content_ja / source 渲染

## 影響範圍

- `backend/data/sukuyodo_mansions.json` (key_concepts + ryouhan_knowledge 資料)
- `frontend/src/components/KnowledgeTab.vue` (key_concepts 模板)

## 測試計畫

1. vite build 零錯誤
2. 知識 → 沿革頁面：核心概念三項皆顯示漢文原典、日文、正體中文、出處
3. 知識 → 凌犯逆轉頁面：底部顯示出處標記
