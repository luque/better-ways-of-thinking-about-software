"""
Tests of the LMS XBlock Runtime and associated utilities
"""


from unittest.mock import Mock, patch
from urllib.parse import urlparse

import pytest
from ddt import data, ddt
from django.conf import settings
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import BlockUsageLocator, CourseLocator
from xblock.exceptions import NoSuchServiceError
from xblock.fields import ScopeIds

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.badges.tests.factories import BadgeClassFactory
from lms.djangoapps.badges.tests.test_models import get_image
from lms.djangoapps.lms_xblock.runtime import LmsModuleSystem
from xmodule.modulestore.django import ModuleI18nService
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class BlockMock(Mock):
    """Mock class that we fill with our "handler" methods."""

    def handler(self, _context):
        """
        A test handler method.
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass

    def handler1(self, _context):
        """
        A test handler method.
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass

    def handler_a(self, _context):
        """
        A test handler method.
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass

    @property
    def location(self):
        """Create a functional BlockUsageLocator for testing URL generation."""
        course_key = CourseLocator(org="mockx", course="100", run="2015")
        return BlockUsageLocator(course_key, block_type='mock_type', block_id="mock_id")


class TestHandlerUrl(TestCase):
    """Test the LMS handler_url"""

    def setUp(self):
        super().setUp()
        self.block = BlockMock(name='block', scope_ids=ScopeIds(None, None, None, 'dummy'))
        self.course_key = CourseLocator("org", "course", "run")
        self.runtime = LmsModuleSystem(
            static_url='/static',
            track_function=Mock(),
            get_module=Mock(),
            render_template=Mock(),
            replace_urls=str,
            course_id=self.course_key,
            descriptor_runtime=Mock(),
        )

    def test_trailing_characters(self):
        assert not self.runtime.handler_url(self.block, 'handler').endswith('?')
        assert not self.runtime.handler_url(self.block, 'handler').endswith('/')

        assert not self.runtime.handler_url(self.block, 'handler', 'suffix').endswith('?')
        assert not self.runtime.handler_url(self.block, 'handler', 'suffix').endswith('/')

        assert not self.runtime.handler_url(self.block, 'handler', 'suffix', 'query').endswith('?')
        assert not self.runtime.handler_url(self.block, 'handler', 'suffix', 'query').endswith('/')

        assert not self.runtime.handler_url(self.block, 'handler', query='query').endswith('?')
        assert not self.runtime.handler_url(self.block, 'handler', query='query').endswith('/')

    def _parsed_query(self, query_string):
        """Return the parsed query string from a handler_url generated with the supplied query_string"""
        return urlparse(self.runtime.handler_url(self.block, 'handler', query=query_string)).query

    def test_query_string(self):
        assert 'foo=bar' in self._parsed_query('foo=bar')
        assert 'foo=bar&baz=true' in self._parsed_query('foo=bar&baz=true')
        assert 'foo&bar&baz' in self._parsed_query('foo&bar&baz')

    def _parsed_path(self, handler_name='handler', suffix=''):
        """Return the parsed path from a handler_url with the supplied handler_name and suffix"""
        return urlparse(self.runtime.handler_url(self.block, handler_name, suffix=suffix)).path

    def test_suffix(self):
        assert self._parsed_path(suffix='foo').endswith('foo')
        assert self._parsed_path(suffix='foo/bar').endswith('foo/bar')
        assert self._parsed_path(suffix='/foo/bar').endswith('/foo/bar')

    def test_handler_name(self):
        assert 'handler1' in self._parsed_path('handler1')
        assert 'handler_a' in self._parsed_path('handler_a')

    def test_thirdparty_fq(self):
        """Testing the Fully-Qualified URL returned by thirdparty=True"""
        parsed_fq_url = urlparse(self.runtime.handler_url(self.block, 'handler', thirdparty=True))
        assert parsed_fq_url.scheme == 'https'
        assert parsed_fq_url.hostname == settings.SITE_NAME

    def test_not_thirdparty_rel(self):
        """Testing the Fully-Qualified URL returned by thirdparty=False"""
        parsed_fq_url = urlparse(self.runtime.handler_url(self.block, 'handler', thirdparty=False))
        assert parsed_fq_url.scheme == ''
        assert parsed_fq_url.hostname is None


class TestUserServiceAPI(TestCase):
    """Test the user service interface"""

    def setUp(self):
        super().setUp()
        self.course_id = CourseLocator("org", "course", "run")
        self.user = UserFactory.create()

        def mock_get_real_user(_anon_id):
            """Just returns the test user"""
            return self.user

        self.runtime = LmsModuleSystem(
            static_url='/static',
            track_function=Mock(),
            get_module=Mock(),
            render_template=Mock(),
            replace_urls=str,
            course_id=self.course_id,
            get_real_user=mock_get_real_user,
            descriptor_runtime=Mock(),
        )
        self.scope = 'course'
        self.key = 'key1'

        self.mock_block = Mock()
        self.mock_block.service_declaration.return_value = 'needs'

    def test_get_set_tag(self):
        # test for when we haven't set the tag yet
        tag = self.runtime.service(self.mock_block, 'user_tags').get_tag(self.scope, self.key)
        assert tag is None

        # set the tag
        set_value = 'value'
        self.runtime.service(self.mock_block, 'user_tags').set_tag(self.scope, self.key, set_value)
        tag = self.runtime.service(self.mock_block, 'user_tags').get_tag(self.scope, self.key)

        assert tag == set_value

        # Try to set tag in wrong scope
        with pytest.raises(ValueError):
            self.runtime.service(self.mock_block, 'user_tags').set_tag('fake_scope', self.key, set_value)

        # Try to get tag in wrong scope
        with pytest.raises(ValueError):
            self.runtime.service(self.mock_block, 'user_tags').get_tag('fake_scope', self.key)


@ddt
class TestBadgingService(ModuleStoreTestCase):
    """Test the badging service interface"""

    def setUp(self):
        super().setUp()
        self.course_id = CourseKey.from_string('course-v1:org+course+run')

        self.mock_block = Mock()
        self.mock_block.service_declaration.return_value = 'needs'

    def create_runtime(self):
        """
        Create the testing runtime.
        """
        def mock_get_real_user(_anon_id):
            """Just returns the test user"""
            return self.user

        return LmsModuleSystem(
            static_url='/static',
            track_function=Mock(),
            get_module=Mock(),
            render_template=Mock(),
            replace_urls=str,
            course_id=self.course_id,
            get_real_user=mock_get_real_user,
            descriptor_runtime=Mock(),
        )

    @patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
    def test_service_rendered(self):
        runtime = self.create_runtime()
        assert runtime.service(self.mock_block, 'badging')

    @patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': False})
    def test_no_service_rendered(self):
        runtime = self.create_runtime()
        assert not runtime.service(self.mock_block, 'badging')

    @data(True, False)
    @patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
    def test_course_badges_toggle(self, toggle):
        self.course_id = CourseFactory.create(metadata={'issue_badges': toggle}).location.course_key
        runtime = self.create_runtime()
        assert runtime.service(self.mock_block, 'badging').course_badges_enabled is toggle

    @patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
    def test_get_badge_class(self):
        runtime = self.create_runtime()
        badge_service = runtime.service(self.mock_block, 'badging')
        premade_badge_class = BadgeClassFactory.create()
        # Ignore additional parameters. This class already exists.
        # We should get back the first class we created, rather than a new one.
        badge_class = badge_service.get_badge_class(
            slug='test_slug', issuing_component='test_component', description='Attempted override',
            criteria='test', display_name='Testola', image_file_handle=get_image('good')
        )
        # These defaults are set on the factory.
        assert badge_class.criteria == 'https://example.com/syllabus'
        assert badge_class.display_name == 'Test Badge'
        assert badge_class.description == "Yay! It's a test badge."
        # File name won't always be the same.
        assert badge_class.image.path == premade_badge_class.image.path


class TestI18nService(ModuleStoreTestCase):
    """ Test ModuleI18nService """

    def setUp(self):
        """ Setting up tests """
        super().setUp()
        self.course = CourseFactory.create()
        self.test_language = 'dummy language'
        self.runtime = LmsModuleSystem(
            static_url='/static',
            track_function=Mock(),
            get_module=Mock(),
            render_template=Mock(),
            replace_urls=str,
            course_id=self.course.id,
            descriptor_runtime=Mock(),
        )

        self.mock_block = Mock()
        self.mock_block.service_declaration.return_value = 'need'

    def test_module_i18n_lms_service(self):
        """
        Test: module i18n service in LMS
        """
        i18n_service = self.runtime.service(self.mock_block, 'i18n')
        assert i18n_service is not None
        assert isinstance(i18n_service, ModuleI18nService)

    def test_no_service_exception_with_none_declaration_(self):
        """
        Test: NoSuchServiceError should be raised block declaration returns none
        """
        self.mock_block.service_declaration.return_value = None
        with pytest.raises(NoSuchServiceError):
            self.runtime.service(self.mock_block, 'i18n')

    def test_no_service_exception_(self):
        """
        Test: NoSuchServiceError should be raised if i18n service is none.
        """
        self.runtime._services['i18n'] = None  # pylint: disable=protected-access
        with pytest.raises(NoSuchServiceError):
            self.runtime.service(self.mock_block, 'i18n')

    def test_i18n_service_callable(self):
        """
        Test: _services dict should contain the callable i18n service in LMS.
        """
        assert callable(self.runtime._services.get('i18n'))  # pylint: disable=protected-access

    def test_i18n_service_not_callable(self):
        """
        Test: i18n service should not be callable in LMS after initialization.
        """
        assert not callable(self.runtime.service(self.mock_block, 'i18n'))
