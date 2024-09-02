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

import logging

from functools import wraps
from typing import Callable, Optional, Any
from github import GithubException
from requests.exceptions import Timeout, RequestException, ConnectionError as RequestsConnectionError
from release_notes_generator.utils.github_rate_limiter import GithubRateLimiter


def debug_log_decorator(method: Callable) -> Callable:
    """
    Decorator to add debug logging for a method call.
    """
    @wraps(method)
    def wrapped(*args, **kwargs) -> Optional[Any]:
        logging.debug("Calling method %s with args: %s and kwargs: %s", method.__name__, args, kwargs)
        result = method(*args, **kwargs)
        logging.debug("Method %s returned %s", method.__name__, result)
        return result
    return wrapped


# pylint: disable=broad-except
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
            except (RequestsConnectionError, Timeout) as e:
                logging.error("Network error calling %s: %s", method.__name__, e, exc_info=True)
                return None
            except GithubException as e:
                logging.error("GitHub API error calling %s: %s", method.__name__, e, exc_info=True)
                return None
            except RequestException as e:
                logging.error("HTTP error calling %s: %s", method.__name__, e, exc_info=True)
                return None
            except Exception as e:
                logging.error("Unexpected error calling %s: %s", method.__name__, e, exc_info=True)
                return None
        return wrapped
    return decorator
