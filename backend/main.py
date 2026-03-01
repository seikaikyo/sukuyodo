"""
Sukuyodo API - 宿曜道占星術服務

基於空海《宿曜經》的日本真言宗占星術系統
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from database import init_db
from routers import sukuyodo

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期"""
    # 啟動時初始化資料庫
    init_db()
    yield
    # 關閉時清理資源


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="宿曜道 - 日本真言宗宿曜占星術 API",
    lifespan=lifespan,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(sukuyodo.router, prefix="/api/sukuyodo", tags=["Sukuyodo"])


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "healthy"}
