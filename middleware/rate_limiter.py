"""
Rate Limiter Middleware
==================
Simple in-memory rate limiter (use Redis for production).
"""
import time
from collections import defaultdict
from fastapi import HTTPException, Request

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def check(self, key: str):
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if t > minute_ago]
        
        if len(self.requests[key]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later."
            )
        
        self.requests[key].append(now)

rate_limiter = RateLimiter(requests_per_minute=60)

async def rate_limit(request: Request):
    """Dependency for rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(client_ip)
