"""
Test the retire_user management command
"""


import pytest
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.management import CommandError, call_command

from ...models import UserRetirementStatus
from openedx.core.djangoapps.user_api.accounts.tests.retirement_helpers import (  # lint-amnesty, pylint: disable=unused-import, wrong-import-order
    setup_retirement_states
)
from openedx.core.djangolib.testing.utils import skip_unless_lms  # lint-amnesty, pylint: disable=wrong-import-order
from common.djangoapps.student.tests.factories import UserFactory  # lint-amnesty, pylint: disable=wrong-import-order


pytestmark = pytest.mark.django_db


@skip_unless_lms
def test_successful_retire(setup_retirement_states):  # lint-amnesty, pylint: disable=redefined-outer-name, unused-argument
    user = UserFactory()
    username = user.username
    user_email = user.email
    call_command('retire_user', username=username, user_email=user_email)
    user = User.objects.get(username=username)
    retired_user_status = UserRetirementStatus.objects.all()[0]
    assert retired_user_status.original_username == username
    assert retired_user_status.original_email == user_email
    # Make sure that we have changed the email address linked to the original user
    assert user.email != user_email


@skip_unless_lms
def test_retire_user_with_usename_email_mismatch(setup_retirement_states):  # lint-amnesty, pylint: disable=redefined-outer-name, unused-argument
    user = UserFactory()
    username = user.username
    user_email = "other@edx.org"
    with pytest.raises(CommandError, match=r'Could not find a user with specified username and email address'):
        call_command('retire_user', username=username, user_email=user_email)
