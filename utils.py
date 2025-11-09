# utils.py
import asyncio
from loguru import logger

class RateLimiter:
    """Simple token-bucket style limiter."""
    def __init__(self, per_second: float):
        self.delay = 1.0 / per_second
        self.last = 0.0
        self.lock = asyncio.Lock()

    async def __aenter__(self):
        async with self.lock:
            now = asyncio.get_event_loop().time()
            await asyncio.sleep(max(0, self.delay - (now - self.last)))
            self.last = asyncio.get_event_loop().time()

    async def __aexit__(self, *args):
        pass
