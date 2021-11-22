"""
Tests for the DjangoXBlockUserService.
"""

import pytest
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.djangoapps.external_user_ids.models import ExternalIdType
from common.djangoapps.student.models import anonymous_id_for_user
from common.djangoapps.student.tests.factories import AnonymousUserFactory, UserFactory
from common.djangoapps.xblock_django.user_service import (
    ATTR_KEY_IS_AUTHENTICATED,
    ATTR_KEY_USER_ID,
    ATTR_KEY_USER_IS_STAFF,
    ATTR_KEY_USER_PREFERENCES,
    ATTR_KEY_USERNAME,
    USER_PREFERENCES_WHITE_LIST,
    DjangoXBlockUserService
)


class UserServiceTestCase(TestCase):
    """
    Tests for the DjangoXBlockUserService.
    """
    def setUp(self):
        super().setUp()
        self.user = UserFactory(username="tester", email="test@tester.com")
        self.user.profile.name = "Test Tester"
        set_user_preference(self.user, 'pref-lang', 'en')
        set_user_preference(self.user, 'time_zone', 'US/Pacific')
        set_user_preference(self.user, 'not_white_listed', 'hidden_value')
        self.anon_user = AnonymousUserFactory()

    def assert_is_anon_xb_user(self, xb_user):
        """
        A set of assertions for an anonymous XBlockUser.
        """
        assert not xb_user.opt_attrs[ATTR_KEY_IS_AUTHENTICATED]
        assert xb_user.full_name is None
        self.assertListEqual(xb_user.emails, [])

    def assert_xblock_user_matches_django(self, xb_user, dj_user):
        """
        A set of assertions for comparing a XBlockUser to a django User
        """
        assert xb_user.opt_attrs[ATTR_KEY_IS_AUTHENTICATED]
        assert xb_user.emails[0] == dj_user.email
        assert xb_user.full_name == dj_user.profile.name
        assert xb_user.opt_attrs[ATTR_KEY_USERNAME] == dj_user.username
        assert xb_user.opt_attrs[ATTR_KEY_USER_ID] == dj_user.id
        assert not xb_user.opt_attrs[ATTR_KEY_USER_IS_STAFF]
        assert all((pref in USER_PREFERENCES_WHITE_LIST) for pref in xb_user.opt_attrs[ATTR_KEY_USER_PREFERENCES])

    def test_convert_anon_user(self):
        """
        Tests for convert_django_user_to_xblock_user behavior when django user is AnonymousUser.
        """
        django_user_service = DjangoXBlockUserService(self.anon_user)
        xb_user = django_user_service.get_current_user()
        assert xb_user.is_current_user
        self.assert_is_anon_xb_user(xb_user)

    def test_convert_authenticate_user(self):
        """
        Tests for convert_django_user_to_xblock_user behavior when django user is User.
        """
        django_user_service = DjangoXBlockUserService(self.user)
        xb_user = django_user_service.get_current_user()
        assert xb_user.is_current_user
        self.assert_xblock_user_matches_django(xb_user, self.user)

    def test_get_anonymous_user_id_returns_none_for_non_staff_users(self):
        """
        Tests for anonymous_user_id method to return None if user is Non-Staff.
        """
        django_user_service = DjangoXBlockUserService(self.user, user_is_staff=False)

        anonymous_user_id = django_user_service.get_anonymous_user_id(
            username=self.user.username,
            course_id='edx/toy/2012_Fall'
        )
        assert anonymous_user_id is None

    def test_get_anonymous_user_id_returns_none_for_non_existing_users(self):
        """
        Tests for anonymous_user_id method to return None username does not exist in system.
        """
        django_user_service = DjangoXBlockUserService(self.user, user_is_staff=True)

        anonymous_user_id = django_user_service.get_anonymous_user_id(username="No User", course_id='edx/toy/2012_Fall')
        assert anonymous_user_id is None

    def test_get_anonymous_user_id_returns_id_for_existing_users(self):
        """
        Tests for anonymous_user_id method returns anonymous user id for a user.
        """
        course_key = CourseKey.from_string('edX/toy/2012_Fall')
        anon_user_id = anonymous_id_for_user(
            user=self.user,
            course_id=course_key
        )

        django_user_service = DjangoXBlockUserService(self.user, user_is_staff=True)
        anonymous_user_id = django_user_service.get_anonymous_user_id(
            username=self.user.username,
            course_id='edX/toy/2012_Fall'
        )

        assert anonymous_user_id == anon_user_id

    def test_external_id(self):
        """
        Tests that external ids differ based on type.
        """
        ExternalIdType.objects.create(name='test1', description='Test type 1')
        ExternalIdType.objects.create(name='test2', description='Test type 2')
        django_user_service = DjangoXBlockUserService(self.user, user_is_staff=True)
        ext_id1 = django_user_service.get_external_user_id('test1')
        ext_id2 = django_user_service.get_external_user_id('test2')
        assert ext_id1 != ext_id2
        with pytest.raises(ValueError):
            django_user_service.get_external_user_id('unknown')
