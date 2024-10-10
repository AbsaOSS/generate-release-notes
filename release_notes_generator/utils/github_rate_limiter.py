#
# Copyright 2023 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
This module contains the GithubRateLimiter class which is responsible for rate limiting the GitHub API calls.
"""

import logging
import time
from datetime import datetime
from typing import Optional, Callable
from github import Github

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class GithubRateLimiter:
    """
    A class used to rate limit the GitHub API calls.
    """

    def __init__(self, github_client: Github):
        self.github_client = github_client

    def __call__(self, method: Callable) -> Callable:
        """
        Decorator to rate limit the GitHub API calls.

        @param method: The method to decorate.
        @return: The decorated method.
        """

        def wrapped_method(*args, **kwargs) -> Optional:
            # rate_limit = self.github_client.get_rate_limit().core
            remaining_calls = self.github_client.get_rate_limit().core.remaining
            reset_time = self.github_client.get_rate_limit().core.reset.timestamp()

            logger.debug("Remaining calls: %s", remaining_calls)

            if remaining_calls < 5:
                logger.info("Rate limit almost reached. Sleeping until reset time.")
                sleep_time = reset_time - (now := time.time())
                while sleep_time <= 0:
                    # Note: received values can be in the past, so the time shift to 1st positive value is needed
                    reset_time += 3600  # Add 1 hour in seconds
                    sleep_time = reset_time - now

                total_sleep_time = sleep_time + 5  # Total sleep time including the additional 5 seconds
                hours, remainder = divmod(total_sleep_time, 3600)
                minutes, seconds = divmod(remainder, 60)

                logger.info(
                    "Sleeping for %s hours, %s minutes, and %s seconds until %s.",
                    hours,
                    minutes,
                    seconds,
                    datetime.fromtimestamp(reset_time).strftime("%Y-%m-%d %H:%M:%S"),
                )
                time.sleep(sleep_time + 5)  # Sleep for the calculated time plus 5 seconds

            return method(*args, **kwargs)

        return wrapped_method
