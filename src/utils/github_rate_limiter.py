import logging
import time
from datetime import datetime
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
                logging.info("Rate limit almost reached. Sleeping until reset time.")
                sleep_time = reset_time - (now := time.time())
                while sleep_time <= 0:
                    # Note: received values can be in the past, so the time shift to 1st positive value is needed
                    reset_time += 3600  # Add 1 hour in seconds
                    sleep_time = reset_time - now

                total_sleep_time = sleep_time + 5  # Total sleep time including the additional 5 seconds
                hours, remainder = divmod(total_sleep_time, 3600)
                minutes, seconds = divmod(remainder, 60)

                logging.info(f"Sleeping for {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds until {datetime.fromtimestamp(reset_time).strftime('%Y-%m-%d %H:%M:%S')}.")
                time.sleep(sleep_time + 5)  # Sleep for the calculated time plus 5 seconds

            return method(*args, **kwargs)

        return wrapped_method
