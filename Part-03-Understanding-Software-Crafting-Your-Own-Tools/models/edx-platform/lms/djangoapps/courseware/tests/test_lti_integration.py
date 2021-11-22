"""LTI integration tests"""


import json
from collections import OrderedDict

from unittest import mock
import urllib
import oauthlib
from django.conf import settings
from django.urls import reverse

from lms.djangoapps.courseware.tests.helpers import BaseTestXmodule
from lms.djangoapps.courseware.views.views import get_course_lti_endpoints
from openedx.core.lib.url_utils import quote_slashes
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.x_module import STUDENT_VIEW


class TestLTI(BaseTestXmodule):
    """
    Integration test for lti xmodule.

    It checks overall code, by assuring that context that goes to template is correct.
    As part of that, checks oauth signature generation by mocking signing function
    of `oauthlib` library.
    """
    CATEGORY = "lti"

    def setUp(self):
        """
        Mock oauth1 signing of requests library for testing.
        """
        super().setUp()
        mocked_nonce = '135685044251684026041377608307'
        mocked_timestamp = '1234567890'
        mocked_signature_after_sign = 'my_signature%3D'
        mocked_decoded_signature = 'my_signature='

        # Note: this course_id is actually a course_key
        context_id = str(self.item_descriptor.course_id)
        user_id = str(self.item_descriptor.xmodule_runtime.anonymous_student_id)
        hostname = self.item_descriptor.xmodule_runtime.hostname
        resource_link_id = str(urllib.parse.quote(f'{hostname}-{self.item_descriptor.location.html_id()}'))

        sourcedId = "{context}:{resource_link}:{user_id}".format(
            context=urllib.parse.quote(context_id),
            resource_link=resource_link_id,
            user_id=user_id
        )

        self.correct_headers = {
            'user_id': user_id,
            'oauth_callback': 'about:blank',
            'launch_presentation_return_url': '',
            'lti_message_type': 'basic-lti-launch-request',
            'lti_version': 'LTI-1p0',
            'roles': 'Student',
            'context_id': context_id,

            'resource_link_id': resource_link_id,
            'lis_result_sourcedid': sourcedId,

            'oauth_nonce': mocked_nonce,
            'oauth_timestamp': mocked_timestamp,
            'oauth_consumer_key': '',
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_version': '1.0',
            'oauth_signature': mocked_decoded_signature
        }

        saved_sign = oauthlib.oauth1.Client.sign

        self.expected_context = {
            'display_name': self.item_descriptor.display_name,
            'input_fields': self.correct_headers,
            'element_class': self.item_descriptor.category,
            'element_id': self.item_descriptor.location.html_id(),
            'launch_url': 'http://www.example.com',  # default value
            'open_in_a_new_page': True,
            'form_url': self.item_descriptor.xmodule_runtime.handler_url(self.item_descriptor,
                                                                         'preview_handler').rstrip('/?'),
            'hide_launch': False,
            'has_score': False,
            'module_score': None,
            'comment': '',
            'weight': 1.0,
            'ask_to_send_username': self.item_descriptor.ask_to_send_username,
            'ask_to_send_email': self.item_descriptor.ask_to_send_email,
            'description': self.item_descriptor.description,
            'button_text': self.item_descriptor.button_text,
            'accept_grades_past_due': self.item_descriptor.accept_grades_past_due,
        }

        def mocked_sign(self, *args, **kwargs):
            """
            Mocked oauth1 sign function.
            """
            # self is <oauthlib.oauth1.rfc5849.Client object> here:
            __, headers, __ = saved_sign(self, *args, **kwargs)
            # we should replace nonce, timestamp and signed_signature in headers:
            old = headers['Authorization']
            old_parsed = OrderedDict([param.strip().replace('"', '').split('=') for param in old.split(',')])
            old_parsed['OAuth oauth_nonce'] = mocked_nonce
            old_parsed['oauth_timestamp'] = mocked_timestamp
            old_parsed['oauth_signature'] = mocked_signature_after_sign
            headers['Authorization'] = ', '.join([k + '="' + v + '"' for k, v in old_parsed.items()])
            return None, headers, None

        patcher = mock.patch.object(oauthlib.oauth1.Client, "sign", mocked_sign)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_lti_constructor(self):
        generated_content = self.item_descriptor.render(STUDENT_VIEW).content
        expected_content = self.runtime.render_template('lti.html', self.expected_context)
        assert generated_content == expected_content

    def test_lti_preview_handler(self):
        generated_content = self.item_descriptor.preview_handler(None, None).body
        expected_content = self.runtime.render_template('lti_form.html', self.expected_context)
        assert generated_content.decode('utf-8') == expected_content


class TestLTIBlockListing(SharedModuleStoreTestCase):
    """
    a test for the rest endpoint that lists LTI modules in a course
    """
    # arbitrary constant
    COURSE_SLUG = "100"
    COURSE_NAME = "test_course"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create(display_name=cls.COURSE_NAME, number=cls.COURSE_SLUG)
        cls.chapter1 = ItemFactory.create(
            parent_location=cls.course.location,
            display_name="chapter1",
            category='chapter')
        cls.section1 = ItemFactory.create(
            parent_location=cls.chapter1.location,
            display_name="section1",
            category='sequential')
        cls.chapter2 = ItemFactory.create(
            parent_location=cls.course.location,
            display_name="chapter2",
            category='chapter')
        cls.section2 = ItemFactory.create(
            parent_location=cls.chapter2.location,
            display_name="section2",
            category='sequential')

        # creates one draft and one published lti module, in different sections
        cls.lti_published = ItemFactory.create(
            parent_location=cls.section1.location,
            display_name="lti published",
            category="lti",
            location=cls.course.id.make_usage_key('lti', 'lti_published'),
        )
        cls.lti_draft = ItemFactory.create(
            parent_location=cls.section2.location,
            display_name="lti draft",
            category="lti",
            location=cls.course.id.make_usage_key('lti', 'lti_draft'),
            publish_item=False,
        )

    def expected_handler_url(self, handler):
        """convenience method to get the reversed handler urls"""
        return "https://{}{}".format(settings.SITE_NAME, reverse(
            'xblock_handler_noauth',
            args=[
                str(self.course.id),
                quote_slashes(str(self.lti_published.scope_ids.usage_id)),
                handler
            ]
        ))

    def test_lti_rest_bad_course(self):
        """Tests what happens when the lti listing rest endpoint gets a bad course_id"""
        bad_ids = ["sf", "dne/dne/dne", "fo/ey/\\u5305"]
        for bad_course_id in bad_ids:
            lti_rest_endpoints_url = f'courses/{bad_course_id}/lti_rest_endpoints/'
            response = self.client.get(lti_rest_endpoints_url)
            assert 404 == response.status_code

    def test_lti_rest_listing(self):
        """tests that the draft lti module is part of the endpoint response"""
        request = mock.Mock()
        request.method = 'GET'
        response = get_course_lti_endpoints(request, course_id=str(self.course.id))

        assert 200 == response.status_code
        assert 'application/json' == response['Content-Type']

        expected = {
            "lti_1_1_result_service_xml_endpoint": self.expected_handler_url('grade_handler'),
            "lti_2_0_result_service_json_endpoint":
            self.expected_handler_url('lti_2_0_result_rest_handler') + "/user/{anon_user_id}",
            "display_name": self.lti_published.display_name,
        }
        assert [expected] == json.loads(response.content.decode('utf-8'))

    def test_lti_rest_non_get(self):
        """tests that the endpoint returns 404 when hit with NON-get"""
        DISALLOWED_METHODS = ("POST", "PUT", "DELETE", "HEAD", "OPTIONS")  # pylint: disable=invalid-name
        for method in DISALLOWED_METHODS:
            request = mock.Mock()
            request.method = method
            response = get_course_lti_endpoints(request, str(self.course.id))
            assert 405 == response.status_code
