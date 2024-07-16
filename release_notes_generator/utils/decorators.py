import logging

from typing import Callable, Optional, Any
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter
from functools import wraps


def debug_log_decorator(method: Callable) -> Callable:
    """
    Decorator to add debug logging for a method call.
    """
    @wraps(method)
    def wrapped(*args, **kwargs) -> Optional[Any]:
        logging.debug(f"Calling method {method.__name__} with args: {args} and kwargs: {kwargs}")
        result = method(*args, **kwargs)
        logging.debug(f"Method {method.__name__} returned {result}")
        return result
    return wrapped


def safe_call_decorator(rate_limiter: GithubRateLimiter):
    """
    Decorator factory to create a rate-limited safe call function.
    """
    def decorator(method: Callable) -> Callable:
        # Note: Keep log decorator first to log correct method name.
        @debug_log_decorator
        @wraps(method)
        @rate_limiter
        def wrapped(*args, **kwargs) -> Optional[Any]:
            try:
                return method(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error calling {method.__name__}: {e}", exc_info=True)
                return None
        return wrapped
    return decorator
