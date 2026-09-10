from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import JSON, DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


class CacheEntry(Base):
    __tablename__ = "cache_entries"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    response_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TraceRecord(Base):
    __tablename__ = "traces"
    trace_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    response_json: Mapped[str] = mapped_column(Text)


class TraceSpanRecord(Base):
    __tablename__ = "trace_spans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30))
    started_at_ms: Mapped[float]
    duration_ms: Mapped[float]
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


def make_engine(url: str | None = None):
    database_url = url or get_settings().database_url
    if database_url.startswith("sqlite:///./"):
        Path("data").mkdir(exist_ok=True)
    return create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_session() -> Session:
    return SessionLocal()


def trace_by_id(session: Session, trace_id: str) -> TraceRecord | None:
    return session.scalar(select(TraceRecord).where(TraceRecord.trace_id == trace_id))
