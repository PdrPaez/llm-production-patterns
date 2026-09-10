import math
import threading
import time
from dataclasses import dataclass


@dataclass
class Bucket:
    tokens: float
    updated: float


class TokenBucketLimiter:
    def __init__(self, capacity: int = 5, refill_per_second: float = 1.0):
        self.capacity, self.refill = capacity, refill_per_second
        self.buckets: dict[str, Bucket] = {}
        self.lock = threading.Lock()

    def consume(self, client_id: str) -> dict:
        now = time.monotonic()
        with self.lock:
            bucket = self.buckets.setdefault(client_id, Bucket(self.capacity, now))
            bucket.tokens = min(self.capacity, bucket.tokens + (now - bucket.updated) * self.refill); bucket.updated = now
            if bucket.tokens < 1:
                retry = max(1, math.ceil((1 - bucket.tokens) / self.refill))
                return {"allowed": False, "remaining": int(bucket.tokens), "retry_after": retry}
            bucket.tokens -= 1
            return {"allowed": True, "remaining": int(bucket.tokens), "retry_after": 0}
