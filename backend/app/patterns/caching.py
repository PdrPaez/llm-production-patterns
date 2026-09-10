import hashlib
import json
from datetime import timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..database import CacheEntry, utcnow


def cache_key(request: dict, provider: str) -> str:
    canonical = {"provider": provider, **request}
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def get_cached(session: Session, key: str, ttl_seconds: int):
    entry = session.scalar(select(CacheEntry).where(CacheEntry.key == key))
    if not entry:
        return None
    created_at = entry.created_at.replace(tzinfo=None)
    if utcnow().replace(tzinfo=None) - created_at > timedelta(seconds=ttl_seconds):
        session.delete(entry); session.commit(); return None
    return json.loads(entry.response_json)


def put_cached(session: Session, key: str, response: dict) -> None:
    session.merge(CacheEntry(key=key, response_json=json.dumps(response), created_at=utcnow())); session.commit()


def clear_cache(session: Session) -> int:
    count = session.scalar(select(func.count()).select_from(CacheEntry)) or 0
    session.execute(delete(CacheEntry)); session.commit(); return count


def cache_stats(session: Session) -> dict:
    return {"entries": session.scalar(select(func.count()).select_from(CacheEntry)) or 0}
