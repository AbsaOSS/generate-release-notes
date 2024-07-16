def test_rate_limiter_extended_sleep(mocker, rate_limiter_calls, request):
    # Access the current parameter set
    params = request.getfixturevalue('mock_rate_limiter_calls').core

    # Patch time.sleep to avoid actual delay and track call count
    mock_sleep = mocker.patch('time.sleep', return_value=None)

    # Mock method to be wrapped
    method_mock = mocker.Mock()
    wrapped_method = rate_limiter_calls(method_mock)

    wrapped_method()

    method_mock.assert_called_once()

    if params.remaining == 1:
        mock_sleep.assert_called_once()
    else:
        mock_sleep.assert_not_called()
