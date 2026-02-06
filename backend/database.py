from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import get_settings

# 導入模型以確保 SQLModel 能建立資料表
from models.stats import UsageStats  # noqa: F401

settings = get_settings()


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _build_sync_url(url: str) -> str:
    """產生同步引擎用的 URL"""
    if _is_sqlite(url):
        return url
    return url.replace("postgresql://", "postgresql+psycopg://")


def _build_async_url(url: str) -> str:
    """產生非同步引擎用的 URL"""
    if _is_sqlite(url):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    return url.replace("postgresql://", "postgresql+asyncpg://")


def _build_engine(url: str):
    sync_url = _build_sync_url(url)
    kwargs = {"echo": settings.debug}
    if _is_sqlite(url):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(sync_url, **kwargs)


def _build_async_engine(url: str):
    async_url = _build_async_url(url)
    return create_async_engine(async_url, echo=settings.debug)


# 同步引擎 (用於初始化)
if settings.database_url:
    engine = _build_engine(settings.database_url)
else:
    engine = None

# 非同步引擎 (用於 API 請求)
if settings.database_url:
    async_engine = _build_async_engine(settings.database_url)
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
