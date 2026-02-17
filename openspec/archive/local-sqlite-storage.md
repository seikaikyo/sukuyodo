---
title: 本機開發改用 SQLite 儲存
type: refactor
status: completed
created: 2026-02-06
---

# 本機開發改用 SQLite 儲存

## 變更內容
將本機開發的資料庫從 Docker PostgreSQL 改為 SQLite 檔案儲存，降低資源消耗。
生產環境（Render + Neon PostgreSQL）維持不變，透過 DATABASE_URL 自動判斷。

## 影響範圍
- `backend/database.py` - 依 URL scheme 自動切換 SQLite / PostgreSQL 引擎
- `backend/requirements.txt` - 新增 aiosqlite，asyncpg/psycopg 改為選用
- `backend/.env` - 預設改為 SQLite
- `backend/.env.example` - 更新範例
- `backend/.gitignore` - 忽略 .db 檔案

## 技術細節
- SQLite URL 格式: `sqlite:///./sukuyodo.db`
- 同步引擎: SQLAlchemy 內建 sqlite 支援
- 非同步引擎: `aiosqlite` 套件
- PostgreSQL URL 開頭為 `postgresql://`，SQLite 為 `sqlite:///`
- SQLModel 的 `create_all` 兩者通用

## 測試計畫
1. 移除 Docker PostgreSQL，啟動後端確認自動建表
2. 呼叫 API 確認讀寫正常
3. 確認 .db 檔案產生於 backend/ 目錄

## Checklist
- [ ] database.py 支援 SQLite + PostgreSQL 雙模式
- [ ] requirements.txt 更新依賴
- [ ] .env 改為 SQLite
- [ ] .gitignore 忽略 .db
- [ ] 啟動測試通過
