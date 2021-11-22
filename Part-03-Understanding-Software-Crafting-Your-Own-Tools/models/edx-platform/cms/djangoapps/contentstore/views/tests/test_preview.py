"""
Tests for contentstore.views.preview.py
"""


import re
from unittest import mock

import ddt
from django.test.client import Client, RequestFactory
from xblock.core import XBlock, XBlockAside

from cms.djangoapps.contentstore.utils import reverse_usage_url
from cms.djangoapps.xblock_config.models import StudioConfig
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.test_asides import AsideTestType

from ..preview import _preview_module_system, get_preview_fragment


@ddt.ddt
class GetPreviewHtmlTestCase(ModuleStoreTestCase):
    """
    Tests for get_preview_fragment.

    Note that there are other existing test cases in test_contentstore that indirectly execute
    get_preview_fragment via the xblock RESTful API.
    """
    @XBlockAside.register_temp_plugin(AsideTestType, 'test_aside')
    def test_preview_fragment(self):
        """
        Test for calling get_preview_html. Ensures data-usage-id is correctly set and
        asides are correctly included.
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        html = ItemFactory.create(
            parent_location=course.location,
            category="html",
            data={'data': "<html>foobar</html>"}
        )

        config = StudioConfig.current()
        config.enabled = True
        config.save()

        request = RequestFactory().get('/dummy-url')
        request.user = UserFactory()
        request.session = {}

        # Call get_preview_fragment directly.
        context = {
            'reorderable_items': set(),
            'read_only': True
        }
        html = get_preview_fragment(request, html, context).content

        # Verify student view html is returned, and the usage ID is as expected.
        html_pattern = re.escape(
            str(course.id.make_usage_key('html', 'replaceme'))
        ).replace('replaceme', r'html_[0-9]*')
        self.assertRegex(
            html,
            f'data-usage-id="{html_pattern}"'
        )
        self.assertRegex(html, '<html>foobar</html>')
        self.assertRegex(html, r"data-block-type=[\"\']test_aside[\"\']")
        self.assertRegex(html, "Aside rendered")
        # Now ensure the acid_aside is not in the result
        self.assertNotRegex(html, r"data-block-type=[\"\']acid_aside[\"\']")

        # Ensure about pages don't have asides
        about = modulestore().get_item(course.id.make_usage_key('about', 'overview'))
        html = get_preview_fragment(request, about, context).content
        self.assertNotRegex(html, r"data-block-type=[\"\']test_aside[\"\']")
        self.assertNotRegex(html, "Aside rendered")

    @XBlockAside.register_temp_plugin(AsideTestType, 'test_aside')
    def test_preview_no_asides(self):
        """
        Test for calling get_preview_html. Ensures data-usage-id is correctly set and
        asides are correctly excluded because they are not enabled.
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        html = ItemFactory.create(
            parent_location=course.location,
            category="html",
            data={'data': "<html>foobar</html>"}
        )

        config = StudioConfig.current()
        config.enabled = False
        config.save()

        request = RequestFactory().get('/dummy-url')
        request.user = UserFactory()
        request.session = {}

        # Call get_preview_fragment directly.
        context = {
            'reorderable_items': set(),
            'read_only': True
        }
        html = get_preview_fragment(request, html, context).content

        self.assertNotRegex(html, r"data-block-type=[\"\']test_aside[\"\']")
        self.assertNotRegex(html, "Aside rendered")

    @mock.patch('xmodule.conditional_module.ConditionalBlock.is_condition_satisfied')
    def test_preview_conditional_module_children_context(self, mock_is_condition_satisfied):
        """
        Tests that when empty context is pass to children of ConditionalBlock it will not raise KeyError.
        """
        mock_is_condition_satisfied.return_value = True
        client = Client()
        client.login(username=self.user.username, password=self.user_password)

        with self.store.default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create()

            conditional_block = ItemFactory.create(
                parent_location=course.location,
                category="conditional"
            )

            # child conditional_block
            ItemFactory.create(
                parent_location=conditional_block.location,
                category="conditional"
            )

            url = reverse_usage_url(
                'preview_handler',
                conditional_block.location,
                kwargs={'handler': 'xmodule_handler/conditional_get'}
            )
            response = client.post(url)
            self.assertEqual(response.status_code, 200)

    @ddt.data(ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.mongo)
    def test_block_branch_not_changed_by_preview_handler(self, default_store):
        """
        Tests preview_handler should not update blocks being previewed
        """
        client = Client()
        client.login(username=self.user.username, password=self.user_password)

        with self.store.default_store(default_store):
            course = CourseFactory.create()

            block = ItemFactory.create(
                parent_location=course.location,
                category="problem"
            )

            url = reverse_usage_url(
                'preview_handler',
                block.location,
                kwargs={'handler': 'xmodule_handler/problem_check'}
            )
            response = client.post(url)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(modulestore().has_changes(modulestore().get_item(block.location)))


@XBlock.needs("field-data")
@XBlock.needs("i18n")
@XBlock.needs("user")
@XBlock.needs("teams_configuration")
class PureXBlock(XBlock):
    """
    Pure XBlock to use in tests.
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


@ddt.ddt
class StudioXBlockServiceBindingTest(ModuleStoreTestCase):
    """
    Tests that the Studio Module System (XBlock Runtime) provides an expected set of services.
    """
    def setUp(self):
        """
        Set up the user and request that will be used.
        """
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create()
        self.request = mock.Mock()
        self.field_data = mock.Mock()

    @XBlock.register_temp_plugin(PureXBlock, identifier='pure')
    @ddt.data("user", "i18n", "field-data", "teams_configuration")
    def test_expected_services_exist(self, expected_service):
        """
        Tests that the 'user' and 'i18n' services are provided by the Studio runtime.
        """
        descriptor = ItemFactory(category="pure", parent=self.course)
        runtime = _preview_module_system(
            self.request,
            descriptor,
            self.field_data,
        )
        service = runtime.service(descriptor, expected_service)
        self.assertIsNotNone(service)
