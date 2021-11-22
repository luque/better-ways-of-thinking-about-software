"""
Shared test utilities for Safe Sessions tests
"""


from contextlib import contextmanager
from unittest.mock import patch


class TestSafeSessionsLogMixin:
    """
    Test Mixin class with helpers for testing log method
    calls in the safe sessions middleware.
    """
    @contextmanager
    def assert_logged(self, log_string, log_level='error'):
        """
        Asserts that the logger was called with the given
        log_level and with a regex of the given string.
        """
        with patch('openedx.core.djangoapps.safe_sessions.middleware.log.' + log_level) as mock_log:
            yield
            assert mock_log.called
            self.assertRegex(mock_log.call_args_list[0][0][0], log_string)

    @contextmanager
    def assert_logged_with_message(self, log_string, log_level='error'):
        """
        Asserts that the logger with the given log_level was called
        with a string.
        """
        with patch('openedx.core.djangoapps.safe_sessions.middleware.log.' + log_level) as mock_log:
            yield
            mock_log.assert_any_call(log_string)

    @contextmanager
    def assert_not_logged(self):
        """
        Asserts that the logger was not called with either a warning
        or an error.
        """
        with self.assert_no_error_logged():
            with self.assert_no_warning_logged():
                yield

    @contextmanager
    def assert_no_warning_logged(self):
        """
        Asserts that the logger was not called with a warning.
        """
        with patch('openedx.core.djangoapps.safe_sessions.middleware.log.warning') as mock_log:
            yield
            assert not mock_log.called

    @contextmanager
    def assert_no_error_logged(self):
        """
        Asserts that the logger was not called with an error.
        """
        with patch('openedx.core.djangoapps.safe_sessions.middleware.log.error') as mock_log:
            yield
            assert not mock_log.called

    @contextmanager
    def assert_signature_error_logged(self, sig_error_string):
        """
        Asserts that the logger was called when signature
        verification failed on a SafeCookieData object,
        either because of a parse error or a cryptographic
        failure.

        The sig_error_string is the expected additional
        context logged with the error.
        """
        with self.assert_logged(r'SafeCookieData signature error .*|test_session_id|.*: ' + sig_error_string):
            yield

    @contextmanager
    def assert_incorrect_signature_logged(self):
        """
        Asserts that the logger was called when signature
        verification failed on a SafeCookieData object
        due to a cryptographic failure.
        """
        with self.assert_signature_error_logged('Signature .* does not match'):
            yield

    @contextmanager
    def assert_incorrect_user_logged(self):
        """
        Asserts that the logger was called upon finding that
        the SafeCookieData object is not bound to the expected
        user.
        """
        with self.assert_logged(r'SafeCookieData .* is not bound to user'):
            yield

    @contextmanager
    def assert_parse_error(self):
        """
        Asserts that the logger was called when the
        SafeCookieData object could not be parsed successfully.
        """
        with self.assert_logged('SafeCookieData BWC parse error'):
            yield

    @contextmanager
    def assert_invalid_session_id(self):
        """
        Asserts that the logger was called when a
        SafeCookieData was created with a Falsey value for
        the session_id.
        """
        with self.assert_logged('SafeCookieData not created due to invalid value for session_id'):
            yield

    @contextmanager
    def assert_logged_for_request_user_mismatch(self, user_at_request, user_at_response, log_level, request_path):
        """
        Asserts that warning was logged when request.user
        was not equal to user at response
        """
        with self.assert_logged_with_message(
            (
                "SafeCookieData user at request '{}' does not match user at response: '{}' "
                "for request path '{}'"
            ).format(
                user_at_request, user_at_response, request_path
            ),
            log_level=log_level,
        ):
            yield

    @contextmanager
    def assert_logged_for_session_user_mismatch(self, user_at_request, user_in_session, request_path):
        """
        Asserts that warning was logged when request.user
        was not equal to user at session
        """
        with self.assert_logged_with_message(
            (
                "SafeCookieData user at request '{}' does not match user in session: '{}' "
                "for request path '{}'"
            ).format(
                user_at_request, user_in_session, request_path
            ),
            log_level='warning',
        ):
            yield
