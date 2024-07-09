import asyncio
import time

class RateLimiter:
    def __init__(self, rate: int, per: float = 1.0, burst: int = 1):
        self.rate = rate
        self.per = per
        self.burst = burst
        self.tokens = burst
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            time_passed = now - self.updated_at
            self.tokens += time_passed * (self.rate / self.per)
            if self.tokens > self.burst:
                self.tokens = self.burst
            self.updated_at = now

            if self.tokens < 1:
                sleep_duration = (1 - self.tokens) / (self.rate / self.per)
                await asyncio.sleep(sleep_duration)
                self.tokens = 0
                self.updated_at = time.monotonic()
            else:
                self.tokens -= 1