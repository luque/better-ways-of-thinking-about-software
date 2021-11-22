"""
Helper functions and classes for discussion tests.
"""


import json
from uuid import uuid4


from common.test.acceptance.fixtures import LMS_BASE_URL
from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.fixtures.discussion import (
    ForumsConfigMixin,
    MultipleThreadFixture,
    Thread,
)
from common.test.acceptance.pages.lms.discussion import DiscussionTabSingleThreadPage
from common.test.acceptance.tests.helpers import UniqueCourseTest


class BaseDiscussionMixin:
    """
    A mixin containing methods common to discussion tests.
    """

    def setup_multiple_threads(self, thread_count, **thread_kwargs):
        """
        Set up multiple threads on the page by passing 'thread_count'.
        """
        self.thread_ids = []
        threads = []
        for i in range(thread_count):
            thread_id = f"test_thread_{i}_{uuid4().hex}"
            thread_body = "Dummy long text body." * 50
            threads.append(
                Thread(id=thread_id, commentable_id=self.discussion_id, body=thread_body, **thread_kwargs),
            )
            self.thread_ids.append(thread_id)
        thread_fixture = MultipleThreadFixture(threads)
        response = thread_fixture.push()
        assert response.ok, 'Failed to push discussion content'


class CohortTestMixin:
    """
    Mixin for tests of cohorted courses
    """
    def setup_cohort_config(self, course_fixture, auto_cohort_groups=None):
        """
        Sets up the course to use cohorting with the given list of auto_cohort_groups.
        If auto_cohort_groups is None, no auto cohorts are set.
        """
        course_fixture._update_xblock(course_fixture._course_location, {  # lint-amnesty, pylint: disable=protected-access
            "metadata": {
                "cohort_config": {
                    "auto_cohort_groups": auto_cohort_groups or [],
                    "cohorted_discussions": [],
                    "cohorted": True,
                },
            },
        })

    def add_manual_cohort(self, course_fixture, cohort_name):
        """
        Adds a cohort by name, returning its ID.
        """
        url = LMS_BASE_URL + "/courses/" + course_fixture._course_key + '/cohorts/'  # lint-amnesty, pylint: disable=protected-access
        data = json.dumps({"name": cohort_name, 'assignment_type': 'manual'})
        response = course_fixture.session.post(url, data=data, headers=course_fixture.headers)
        assert response.ok, 'Failed to create cohort'
        return response.json()['id']

    def add_user_to_cohort(self, course_fixture, username, cohort_id):
        """
        Adds a user to the specified cohort.
        """
        url = LMS_BASE_URL + "/courses/" + course_fixture._course_key + f"/cohorts/{cohort_id}/add"  # lint-amnesty, pylint: disable=protected-access
        data = {"users": username}
        course_fixture.headers['Content-type'] = 'application/x-www-form-urlencoded'
        response = course_fixture.session.post(url, data=data, headers=course_fixture.headers)
        assert response.ok, 'Failed to add user to cohort'


class BaseDiscussionTestCase(UniqueCourseTest, ForumsConfigMixin):
    """Base test case class for all discussions-related tests."""
    def setUp(self):
        super().setUp()

        self.discussion_id = f"test_discussion_{uuid4().hex}"
        self.course_fixture = CourseFixture(**self.course_info)
        self.course_fixture.add_children(
            XBlockFixtureDesc("chapter", "Test Section").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc(
                            "discussion",
                            "Test Discussion",
                            metadata={"discussion_id": self.discussion_id}
                        )
                    )
                )
            )
        )
        self.course_fixture.add_advanced_settings(
            {'discussion_topics': {'value': {'General': {'id': 'course'}}}}
        )
        self.course_fixture.install()

        self.enable_forums()

    def create_single_thread_page(self, thread_id):
        """
        Sets up a `DiscussionTabSingleThreadPage` for a given
        `thread_id`.
        """
        return DiscussionTabSingleThreadPage(self.browser, self.course_id, self.discussion_id, thread_id)
