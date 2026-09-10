import time
import uuid

from ..database import TraceRecord, TraceSpanRecord, utcnow
from ..schemas import TraceSpan


class Trace:
    def __init__(self):
        self.trace_id = uuid.uuid4().hex
        self.started = time.perf_counter()
        self.spans: list[TraceSpan] = []

    def span(self, name: str, status: str, metadata: dict | None = None, started_at: float | None = None):
        start = started_at or (time.perf_counter() - self.started) * 1000
        duration = max(0.01, (time.perf_counter() - self.started) * 1000 - start)
        self.spans.append(TraceSpan(name=name, status=status, started_at_ms=start, duration_ms=duration, metadata=metadata or {}))

    def persist(self, session, response: dict) -> None:
        session.add(TraceRecord(trace_id=self.trace_id, created_at=utcnow(), response_json=__import__('json').dumps(response)))
        for span in self.spans:
            session.add(TraceSpanRecord(trace_id=self.trace_id, name=span.name, status=span.status, started_at_ms=span.started_at_ms, duration_ms=span.duration_ms, metadata_json=span.metadata))
        session.commit()
