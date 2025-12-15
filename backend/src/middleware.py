import functools
import time
import logging
import asyncio
from typing import Callable, Any, Dict
from collections import defaultdict

logger = logging.getLogger("mcp_server.middleware")

class RateLimiter:
    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.history: Dict[str, list] = defaultdict(list)
    
    def check(self, key: str) -> bool:
        now = time.time()
        self.history[key] = [t for t in self.history[key] if now - t < self.period]
        if len(self.history[key]) >= self.calls:
            return False
        self.history[key].append(now)
        return True

# Global rate limiter: 60 calls per minute per function (simplified key)
# Ideally we limit per user/token, but context might not be available in decorator easily without inspection
_limiter = RateLimiter(calls=60, period=60.0)

def logged(func: Callable) -> Callable:
    """Decorator to log tool execution start/end/error with timing."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()
        
        # Log request
        # We avoid logging full args if they are sensitive or too huge
        logger.info(f"Tool Request: {func_name}", extra={"event": "tool_start", "tool": func_name})
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
                
            duration = time.time() - start_time
            logger.info(f"Tool Success: {func_name} ({duration:.4f}s)", 
                        extra={"event": "tool_success", "tool": func_name, "duration": duration})
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Tool Error: {func_name} - {str(e)}", 
                         extra={"event": "tool_error", "tool": func_name, "duration": duration, "error": str(e)})
            raise e
            
    return wrapper

def rate_limited(func: Callable) -> Callable:
    """Decorator to limit execution rate."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not _limiter.check(func.__name__):
            logger.warning(f"Rate limit exceeded for {func.__name__}")
            raise Exception("Rate limit exceeded")
            
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
            
    return wrapper
