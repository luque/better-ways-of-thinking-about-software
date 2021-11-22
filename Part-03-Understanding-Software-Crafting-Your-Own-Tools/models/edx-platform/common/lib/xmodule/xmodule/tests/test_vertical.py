"""
Tests for vertical module.
"""

# pylint: disable=protected-access


from collections import namedtuple
from datetime import datetime, timedelta
import json
from unittest.mock import Mock, patch

import pytz
import ddt
from fs.memoryfs import MemoryFS

from . import get_test_system
from .helpers import StubUserService
from .xml import XModuleXmlImportTest
from .xml import factories as xml
from ..x_module import STUDENT_VIEW, AUTHOR_VIEW, PUBLIC_VIEW

COMPLETION_DELAY = 9876

JsonRequest = namedtuple('JsonRequest', ['method', 'body'])


def get_json_request(data):
    """
    Given a data dictionary, return an appropriate JSON request.
    """
    return JsonRequest(
        method='POST',
        body=json.dumps(data),
    )


class StubCompletionService:
    """
    A stub implementation of the CompletionService for testing without access to django
    """

    def __init__(self, enabled, completion_value):
        self._enabled = enabled
        self._completion_value = completion_value
        self.delay = COMPLETION_DELAY

    def completion_tracking_enabled(self):
        """
        Turn on or off completion tracking for clients of the
        StubCompletionService.
        """
        return self._enabled

    def get_completions(self, candidates):
        """
        Return the (dummy) completion values for each specified candidate
        block.
        """
        return {candidate: self._completion_value for candidate in candidates}

    def get_completable_children(self, node):
        return node.get_children()

    def get_complete_on_view_delay_ms(self):
        """
        Return the completion-by-viewing delay in milliseconds.
        """
        return self.delay

    def blocks_to_mark_complete_on_view(self, blocks):
        return {} if self._completion_value == 1.0 else blocks

    def vertical_is_complete(self, item):
        if item.scope_ids.block_type != 'vertical':
            raise ValueError('The passed in xblock is not a vertical type!')
        return self._completion_value == 1 if self._enabled else None


class BaseVerticalBlockTest(XModuleXmlImportTest):
    """
    Tests for the BaseVerticalBlock.
    """
    test_html = 'Test HTML'
    test_problem = 'Test_Problem'
    test_html_nested = 'Nest Nested HTML'
    test_problem_nested = 'Nest_Nested_Problem'

    def setUp(self):
        super().setUp()
        # construct module: course/sequence/vertical - problems
        #                                           \_  nested_vertical / problems
        course = xml.CourseFactory.build()
        sequence = xml.SequenceFactory.build(parent=course)
        vertical = xml.VerticalFactory.build(parent=sequence)

        self.course = self.process_xml(course)
        xml.HtmlFactory(parent=vertical, url_name='test-html', text=self.test_html)
        xml.ProblemFactory(parent=vertical, url_name='test-problem', text=self.test_problem)

        nested_vertical = xml.VerticalFactory.build(parent=vertical)
        xml.HtmlFactory(parent=nested_vertical, url_name='test_html_nested', text=self.test_html_nested)
        xml.ProblemFactory(parent=nested_vertical, url_name='test_problem_nested', text=self.test_problem_nested)

        self.course = self.process_xml(course)
        course_seq = self.course.get_children()[0]
        self.module_system = get_test_system()

        self.module_system.descriptor_runtime = self.course._runtime
        self.course.runtime.export_fs = MemoryFS()

        self.vertical = course_seq.get_children()[0]
        self.vertical.xmodule_runtime = self.module_system

        self.html_block = self.vertical.get_children()[0]
        self.problem_block = self.vertical.get_children()[1]
        self.problem_block.has_score = True
        self.problem_block.graded = True
        self.extra_vertical_block = self.vertical.get_children()[2]  # VerticalBlockWithMixins
        self.nested_problem_block = self.extra_vertical_block.get_children()[1]
        self.nested_problem_block.has_score = True
        self.nested_problem_block.graded = True

        self.username = "bilbo"
        self.default_context = {"bookmarked": False, "username": self.username}


@ddt.ddt
class VerticalBlockTestCase(BaseVerticalBlockTest):
    """
    Tests for the VerticalBlock.
    """

    def assert_bookmark_info(self, assertion, content):
        """
        Assert content has/hasn't all the bookmark info.
        """
        assertion('bookmark_id', content)
        assertion(f'{self.username},{str(self.vertical.location)}', content)
        assertion('bookmarked', content)
        assertion('show_bookmark_button', content)

    @ddt.unpack
    @ddt.data(
        {'context': None, 'view': STUDENT_VIEW, 'completion_value': 0.0, 'days': 1},
        {'context': {}, 'view': STUDENT_VIEW, 'completion_value': 0.0, 'days': 1},
        {'context': {}, 'view': PUBLIC_VIEW, 'completion_value': 0.0, 'days': 1},
        {'context': {'format': 'Quiz'}, 'view': STUDENT_VIEW, 'completion_value': 1.0, 'days': 1},  # completed
        {'context': {'format': 'Exam'}, 'view': STUDENT_VIEW, 'completion_value': 0.0, 'days': 1},  # upcoming
        {'context': {'format': 'Homework'}, 'view': STUDENT_VIEW, 'completion_value': 0.0, 'days': -1},  # past due
    )
    def test_render_student_preview_view(self, context, view, completion_value, days):
        """
        Test the rendering of the student and public view.
        """
        self.module_system._services['bookmarks'] = Mock()
        now = datetime.now(pytz.UTC)
        self.vertical.due = now + timedelta(days=days)
        if view == STUDENT_VIEW:
            self.module_system._services['user'] = StubUserService()
            self.module_system._services['completion'] = StubCompletionService(enabled=True,
                                                                               completion_value=completion_value)
        elif view == PUBLIC_VIEW:
            self.module_system._services['user'] = StubUserService(is_anonymous=True)

        html = self.module_system.render(
            self.vertical, view, self.default_context if context is None else context
        ).content
        assert self.test_html in html
        if view == STUDENT_VIEW:
            assert self.test_problem in html
        else:
            assert self.test_problem not in html
        assert f"'due': datetime.datetime({self.vertical.due.year}, {self.vertical.due.month}, {self.vertical.due.day}"\
               in html
        if view == STUDENT_VIEW:
            self.assert_bookmark_info(self.assertIn, html)
        else:
            self.assert_bookmark_info(self.assertNotIn, html)
        if context:
            assert "'has_assignments': True" in html
            assert "'subsection_format': '{}'".format(context['format']) in html
            assert f"'completed': {completion_value == 1}" in html
            assert f"'past_due': {self.vertical.due < now}" in html

    @ddt.data(True, False)
    def test_render_problem_without_score(self, has_score):
        """
        Test the rendering of the student and public view.
        """
        self.module_system._services['bookmarks'] = Mock()
        self.module_system._services['user'] = StubUserService()
        self.module_system._services['completion'] = StubCompletionService(enabled=True, completion_value=0)

        now = datetime.now(pytz.UTC)
        self.vertical.due = now + timedelta(days=-1)
        self.problem_block.has_score = has_score

        html = self.module_system.render(self.vertical, STUDENT_VIEW, self.default_context).content
        if has_score:
            assert "'has_assignments': True" in html
            assert "'completed': False" in html
            assert "'past_due': True" in html
        else:
            assert "'has_assignments': False" in html
            assert "'completed': None" in html
            assert "'past_due': False" in html

    @ddt.data((True, True), (True, False), (False, True), (False, False))
    @ddt.unpack
    def test_render_access_denied_blocks(self, node_has_access_error, child_has_access_error):
        """ Tests access denied blocks are not rendered when hide_access_error_blocks is True """
        self.module_system._services['bookmarks'] = Mock()
        self.module_system._services['user'] = StubUserService()
        self.vertical.due = datetime.now(pytz.UTC) + timedelta(days=-1)
        self.problem_block.has_access_error = node_has_access_error
        self.nested_problem_block.has_access_error = child_has_access_error

        context = {'username': self.username, 'hide_access_error_blocks': True}
        html = self.module_system.render(self.vertical, STUDENT_VIEW, context).content

        if node_has_access_error and child_has_access_error:
            assert self.test_problem not in html
            assert self.test_problem_nested not in html
        if node_has_access_error and not child_has_access_error:
            assert self.test_problem not in html
            assert self.test_problem_nested in html
        if not node_has_access_error and child_has_access_error:
            assert self.test_problem in html
            assert self.test_problem_nested not in html
        if not node_has_access_error and not child_has_access_error:
            assert self.test_problem in html
            assert self.test_problem_nested in html

    @ddt.data(True, False)
    def test_block_has_access_error(self, has_access_error):
        """ Tests block_has_access_error gives the correct result for child node questions """
        # Use special block from setup (vertical/nested_vertical/problem)
        # has_access_error is set on problem an extra level down, so we have to recurse to pass

        self.nested_problem_block.has_access_error = has_access_error
        should_block = self.vertical.block_has_access_error(self.vertical)

        assert should_block == has_access_error

    @ddt.unpack
    @ddt.data(
        (True, 0.9, True),
        (False, 0.9, False),
        (True, 1.0, False),
    )
    def test_mark_completed_on_view_after_delay_in_context(
            self, completion_enabled, completion_value, mark_completed_enabled
    ):
        """
        Test that mark-completed-on-view-after-delay is only set for relevant child Xblocks.
        """
        with patch.object(self.html_block, 'render') as mock_student_view:
            self.module_system._services['completion'] = StubCompletionService(
                enabled=completion_enabled,
                completion_value=completion_value,
            )
            self.module_system.render(self.vertical, STUDENT_VIEW, self.default_context)
            if mark_completed_enabled:
                assert mock_student_view.call_args[0][1]['wrap_xblock_data']['mark-completed-on-view-after-delay'] ==\
                       9876
            else:
                assert 'wrap_xblock_data' not in mock_student_view.call_args[0][1]

    def test_render_studio_view(self):
        """
        Test the rendering of the Studio author view
        """
        # Vertical shouldn't render children on the unit page
        context = {
            'is_unit_page': True
        }
        html = self.module_system.render(self.vertical, AUTHOR_VIEW, context).content
        assert self.test_html not in html
        assert self.test_problem not in html

        # Vertical should render reorderable children on the container page
        reorderable_items = set()
        context = {
            'is_unit_page': False,
            'reorderable_items': reorderable_items,
        }
        html = self.module_system.render(self.vertical, AUTHOR_VIEW, context).content
        assert self.test_html in html
        assert self.test_problem in html
