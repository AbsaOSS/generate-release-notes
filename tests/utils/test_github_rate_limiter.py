import pytest
from unittest.mock import Mock, patch
import time

from utils.github_rate_limiter import GithubRateLimiter


@pytest.fixture
def github_client_mock():
    return Mock()


@pytest.fixture
def rate_limit_mock():
    return Mock()


@pytest.fixture
def rate_limiter(github_client_mock):
    return GithubRateLimiter(github_client_mock)


def test_rate_limiter_limit_not_met(rate_limiter, github_client_mock, rate_limit_mock):
    # Mock rate limit values
    rate_limit_mock.core.remaining = 10
    rate_limit_mock.core.reset.timestamp.return_value = time.time() + 3600
    github_client_mock.get_rate_limit.return_value = rate_limit_mock

    # Mock method to be wrapped
    method_mock = Mock()
    wrapped_method = rate_limiter(method_mock)

    wrapped_method()
    method_mock.assert_called_once()


@patch('time.sleep', return_value=None)  # Patch sleep to avoid actual delay
def test_rate_limiter_limit_met(sleep_mock, rate_limiter, github_client_mock, rate_limit_mock):
    # Mock rate limit values
    rate_limit_mock.core.remaining = 1
    rate_limit_mock.core.reset.timestamp.return_value = time.time() + 5
    github_client_mock.get_rate_limit.return_value = rate_limit_mock

    # Mock method to be wrapped
    method_mock = Mock()
    wrapped_method = rate_limiter(method_mock)

    wrapped_method()
    method_mock.assert_called_once()
    sleep_mock.assert_called_once()  # Ensure sleep was called


@patch('time.sleep', return_value=None)  # Patch sleep to avoid actual delay
def test_rate_limiter_extended_sleep(sleep_mock, rate_limiter, github_client_mock, rate_limit_mock):
    # Mock rate limit values
    rate_limit_mock.core.remaining = 1
    rate_limit_mock.core.reset.timestamp.return_value = time.time() - 1000
    github_client_mock.get_rate_limit.return_value = rate_limit_mock

    # Mock method to be wrapped
    method_mock = Mock()
    wrapped_method = rate_limiter(method_mock)

    wrapped_method()
    method_mock.assert_called_once()
    sleep_mock.assert_called_once()  # Ensure sleep was called
