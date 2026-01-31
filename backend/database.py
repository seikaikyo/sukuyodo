from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()

# 同步引擎 (用於初始化)
if settings.database_url:
    sync_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://")
    engine = create_engine(sync_url, echo=settings.debug)
else:
    engine = None

# 非同步引擎 (用於 API 請求)
if settings.database_url:
    async_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    async_engine = create_async_engine(async_url, echo=settings.debug)
    AsyncSessionLocal = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
else:
    async_engine = None
    AsyncSessionLocal = None


def init_db():
    """初始化資料庫 (建立資料表)"""
    if engine:
        SQLModel.metadata.create_all(engine)


def get_session():
    """取得同步 Session"""
    if engine is None:
        raise RuntimeError("資料庫未設定")
    with Session(engine) as session:
        yield session


async def get_async_session():
    """取得非同步 Session"""
    if AsyncSessionLocal is None:
        raise RuntimeError("資料庫未設定")
    async with AsyncSessionLocal() as session:
        yield session
