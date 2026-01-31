# Sukuyodo (宿曜道)

日本真言宗宿曜占星術系統

## 功能

- 本命宿查詢（27 宿）
- 雙人相性診斷（六種關係 + 距離類型）
- 每日/每週/每月/每年運勢
- 吉日查詢（求職、搬家、結婚等）

## 技術棧

- **後端**: FastAPI + SQLModel + PostgreSQL
- **前端**: Vite + Vue 3 + Shoelace
- **部署**: Render (後端) + Vercel (前端)

## 本地開發

### 資料庫

```bash
# 啟動資料庫容器
docker start sukuyodo-db

# 連接資料庫
PGPASSWORD=200821 psql -h localhost -p 5433 -U sukuyodo -d sukuyodo
```

### 後端

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 專案結構

```
sukuyodo/
├── backend/           # FastAPI 後端
│   ├── data/          # 靜態資料 (27 宿、關係等)
│   ├── models/        # SQLModel 資料模型
│   ├── routers/       # API 路由
│   ├── services/      # 業務邏輯
│   └── main.py
├── frontend/          # Vue 3 前端
│   ├── src/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── views/
│   │   └── App.vue
│   └── package.json
└── docker-compose.yml
```

## 授權

MIT License
