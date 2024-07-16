from release_notes_generator.utils.decorators import debug_log_decorator, safe_call_decorator


# sample function to be decorated
def sample_function(x, y):
    return x + y


# debug_log_decorator

def test_debug_log_decorator(mocker):
    # Mock logging
    mock_log_debug = mocker.patch('logging.debug')

    decorated_function = debug_log_decorator(sample_function)
    expected_call = [mocker.call(f"Calling method sample_function with args: (3, 4) and kwargs: {{}}"),
                     mocker.call(f"Method sample_function returned 7")]

    result = decorated_function(3, 4)

    assert 7 == result
    assert expected_call == mock_log_debug.call_args_list


# safe_call_decorator

def test_safe_call_decorator_success(rate_limiter):
    @safe_call_decorator(rate_limiter)
    def sample_method(x, y):
        return x + y

    result = sample_method(2, 3)
    assert 5 == result


def test_safe_call_decorator_exception(rate_limiter, mocker):
    mock_log_error = mocker.patch('logging.error')

    @safe_call_decorator(rate_limiter)
    def sample_method(x, y):
        return x / y

    result = sample_method(2, 0)
    assert result is None
    mock_log_error.assert_called_once()
    assert "Error calling sample_method:" in mock_log_error.call_args[0][0]
