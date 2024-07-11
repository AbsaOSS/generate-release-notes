import time
import pytest

from unittest.mock import Mock, patch, call
from utils.decorators import debug_log_decorator, safe_call_decorator
from utils.github_rate_limiter import GithubRateLimiter


# sample function to be decorated
def sample_function(x, y):
    return x + y


@pytest.fixture
def github_client_mock():
    return Mock()


@pytest.fixture
def rate_limit_mock():
    return Mock()


@pytest.fixture
def rate_limiter(github_client_mock):
    return GithubRateLimiter(github_client_mock)


# debug_log_decorator

def test_debug_log_decorator():
    # Mock logging
    with patch('logging.debug') as mock_debug:
        decorated_function = debug_log_decorator(sample_function)
        expected_call = [call(f"Calling method sample_function with args: (3, 4) and kwargs: {{}}"),
                         call(f"Method sample_function returned 7")]

        result = decorated_function(3, 4)

        assert result == 7
        assert expected_call == mock_debug.call_args_list


# safe_call_decorator

def test_safe_call_decorator_success(github_client_mock, rate_limiter, rate_limit_mock):
    rate_limit_mock.core.remaining = 10
    rate_limit_mock.core.reset.timestamp.return_value = time.time() + 3600
    github_client_mock.get_rate_limit.return_value = rate_limit_mock

    @safe_call_decorator(rate_limiter)
    def sample_method(x, y):
        return x + y

    result = sample_method(2, 3)
    assert result == 5


@patch('logging.error')
def test_safe_call_decorator_exception(logging_error_mock, github_client_mock, rate_limiter, rate_limit_mock):
    rate_limit_mock.core.remaining = 10
    rate_limit_mock.core.reset.timestamp.return_value = time.time() + 3600
    github_client_mock.get_rate_limit.return_value = rate_limit_mock

    @safe_call_decorator(rate_limiter)
    def sample_method(x, y):
        return x / y

    result = sample_method(2, 0)
    assert result is None
    logging_error_mock.assert_called_once()
    assert "Error calling sample_method:" in logging_error_mock.call_args[0][0]
