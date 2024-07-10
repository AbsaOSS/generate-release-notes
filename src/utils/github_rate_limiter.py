import time
from typing import Optional, Callable
from github import Github


class GithubRateLimiter:
    def __init__(self, github_client: Github):
        self.github_client = github_client

    def __call__(self, method: Callable) -> Callable:
        def wrapped_method(*args, **kwargs) -> Optional:
            rate_limit = self.github_client.get_rate_limit().core
            remaining_calls = rate_limit.remaining
            reset_time = rate_limit.reset.timestamp()

            if remaining_calls < 5:
                sleep_time = reset_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)

            return method(*args, **kwargs)

        return wrapped_method
