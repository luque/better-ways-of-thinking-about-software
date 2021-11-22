"""
Unit tests for courseware context_processor
"""


from unittest.mock import Mock
from django.contrib.auth.models import AnonymousUser

from lms.djangoapps.courseware.context_processor import user_timezone_locale_prefs
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class UserPrefContextProcessorUnitTest(ModuleStoreTestCase):
    """
    Unit test for courseware context_processor
    """

    def setUp(self):
        super().setUp()

        self.user = UserFactory.create()
        self.request = Mock()
        self.request.user = self.user

    def test_anonymous_user(self):
        self.request.user = AnonymousUser()
        context = user_timezone_locale_prefs(self.request)
        assert context['user_timezone'] is None
        assert context['user_language'] is None

    def test_no_timezone_preference(self):
        set_user_preference(self.user, 'pref-lang', 'en')
        context = user_timezone_locale_prefs(self.request)
        assert context['user_timezone'] is None
        assert context['user_language'] is not None
        assert context['user_language'] == 'en'

    def test_no_language_preference(self):
        set_user_preference(self.user, 'time_zone', 'Asia/Tokyo')
        context = user_timezone_locale_prefs(self.request)
        assert context['user_language'] is None
        assert context['user_timezone'] is not None
        assert context['user_timezone'] == 'Asia/Tokyo'
