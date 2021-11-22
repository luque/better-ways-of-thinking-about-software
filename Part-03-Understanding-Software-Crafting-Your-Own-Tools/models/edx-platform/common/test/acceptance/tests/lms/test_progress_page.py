"""
End-to-end tests for the LMS that utilize the
progress page.
"""


from contextlib import contextmanager
import pytest

from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.common.logout import LogoutPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.problem import ProblemPage
from ...pages.lms.progress import ProgressPage
from ...pages.studio.overview import CourseOutlinePage as StudioCourseOutlinePage
from ..helpers import (
    UniqueCourseTest,
    auto_auth,
    create_multiple_choice_problem,
)


class ProgressPageBaseTest(UniqueCourseTest):
    """
    Provides utility methods for tests retrieving
    scores from the progress page.
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"
    SECTION_NAME = 'Test Section 1'
    SUBSECTION_NAME = 'Test Subsection 1'
    UNIT_NAME = 'Test Unit 1'
    PROBLEM_NAME = 'Test Problem 1'
    PROBLEM_NAME_2 = 'Test Problem 2'

    def setUp(self):
        super().setUp()
        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.problem_page = ProblemPage(self.browser)
        self.progress_page = ProgressPage(self.browser, self.course_id)
        self.logout_page = LogoutPage(self.browser)

        self.studio_course_outline = StudioCourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Install a course with problems
        self.course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        self.problem1 = create_multiple_choice_problem(self.PROBLEM_NAME)
        self.problem2 = create_multiple_choice_problem(self.PROBLEM_NAME_2)

        self.course_fix.add_children(
            XBlockFixtureDesc('chapter', self.SECTION_NAME).add_children(
                XBlockFixtureDesc('sequential', self.SUBSECTION_NAME).add_children(
                    XBlockFixtureDesc('vertical', self.UNIT_NAME).add_children(self.problem1, self.problem2)
                )
            ),
            XBlockFixtureDesc('chapter', "Lab Section").add_children(
                XBlockFixtureDesc('sequential', "Lab Subsection").add_children(
                    XBlockFixtureDesc('vertical', "Lab Unit").add_children(
                        create_multiple_choice_problem("Lab Exercise")
                    )
                )
            )
        ).install()

        # Auto-auth register for the course.
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)

    def _answer_problem_correctly(self):
        """
        Submit a correct answer to the problem.
        """
        self._answer_problem(choice=2)

    def _answer_problem(self, choice):
        """
        Submit the given choice for the problem.
        """
        self.courseware_page.go_to_sequential_position(1)
        self.problem_page.click_choice(f'choice_choice_{choice}')
        self.problem_page.click_submit()

    def _get_section_score(self):
        """
        Return a list of scores from the progress page.
        """
        self.progress_page.visit()
        return self.progress_page.section_score(self.SECTION_NAME, self.SUBSECTION_NAME)  # lint-amnesty, pylint: disable=no-member

    def _get_problem_scores(self):
        """
        Return a list of scores from the progress page.
        """
        self.progress_page.visit()
        return self.progress_page.scores(self.SECTION_NAME, self.SUBSECTION_NAME)  # lint-amnesty, pylint: disable=no-member

    @contextmanager
    def _logged_in_session(self, staff=False):
        """
        Ensure that the user is logged in and out appropriately at the beginning
        and end of the current test.  But if there's an error, don't log out
        before capturing a screenshot.
        """
        self.logout_page.visit()
        if staff:
            auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)
        else:
            auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)
        yield
        self.logout_page.visit()


class SubsectionGradingPolicyBase(ProgressPageBaseTest):
    """
    Base class for testing a subsection and its impact to
    the progress page
    """
    def setUp(self):
        super().setUp()
        self._set_policy_for_subsection("Homework", 0)
        self._set_policy_for_subsection("Lab", 1)

    def _set_policy_for_subsection(self, policy, section=0):
        """
        Set the grading policy for the first subsection in the specified section.
        If a section index is not provided, 0 is assumed.
        """
        with self._logged_in_session(staff=True):
            self.studio_course_outline.visit()
            modal = self.studio_course_outline.section_at(section).subsection_at(0).edit()
            modal.policy = policy
            modal.save()

    def _check_scores_and_page_text(self, problem_scores, section_score, text):
        """
        Asserts that the given problem and section scores, and text,
        appear on the progress page.
        """
        assert self._get_problem_scores() == problem_scores
        assert self._get_section_score() == section_score
        assert self.progress_page.text_on_page(text)  # lint-amnesty, pylint: disable=no-member

    def _check_tick_text(self, index, sr_text, label, label_hidden=True):
        """
        Check the label and sr text for a horizontal (X-axis) tick.
        """
        assert sr_text == self.progress_page.x_tick_sr_text(index)
        assert [label, ('true' if label_hidden else None)] == self.progress_page.x_tick_label(index)


class SubsectionGradingPolicyA11yTest(SubsectionGradingPolicyBase):
    """
    Class to test the accessibility of subsection grading
    """
    a11y = True

    @pytest.mark.skip(reason='This test fails when using the new courseware MFE.')
    def test_axis_a11y(self):
        """
        Tests that the progress chart axes have appropriate a11y (screenreader) markup.
        """
        with self._logged_in_session():
            self.courseware_page.visit()
            # Answer the first HW problem (the unit contains 2 problems, only one will be answered correctly)
            self._answer_problem_correctly()
            self.courseware_page.click_next_button_on_top()
            # Answer the first Lab problem (unit only contains a single problem)
            self._answer_problem_correctly()

            self.progress_page.a11y_audit.config.set_rules({
                "ignore": [
                    'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                    'region',  # TODO: AC-932
                ]
            })
            self.progress_page.visit()

            # Verify the basic a11y of the progress page
            self.progress_page.a11y_audit.check_for_accessibility_errors()

            # Verify that y-Axis labels are aria-hidden
            assert ['100%', 'true'] == self.progress_page.y_tick_label(0)
            assert ['0%', 'true'] == self.progress_page.y_tick_label(1)
            assert ['Pass 50%', 'true'] == self.progress_page.y_tick_label(2)
            # Verify x-Axis labels and sr-text
            self._check_tick_text(0, ['Homework 1 - Test Subsection 1 - 50% (1/2)'], 'HW 01')

            # Homeworks 2-10 are checked in the for loop below.

            self._check_tick_text(
                10,
                ['Homework 11 Unreleased - 0% (?/?)', 'The lowest 2 Homework scores are dropped.'],
                'HW 11'
            )

            self._check_tick_text(
                11,
                ['Homework 12 Unreleased - 0% (?/?)', 'The lowest 2 Homework scores are dropped.'],
                'HW 12'
            )

            self._check_tick_text(12, ['Homework Average = 5%'], 'HW Avg')
            self._check_tick_text(13, ['Lab 1 - Lab Subsection - 100% (1/1)'], 'Lab 01')

            # Labs 2-10 are checked in the for loop below.

            self._check_tick_text(
                23,
                ['Lab 11 Unreleased - 0% (?/?)', 'The lowest 2 Lab scores are dropped.'],
                'Lab 11'
            )
            self._check_tick_text(
                24,
                ['Lab 12 Unreleased - 0% (?/?)', 'The lowest 2 Lab scores are dropped.'],
                'Lab 12'
            )

            self._check_tick_text(25, ['Lab Average = 10%'], 'Lab Avg')
            self._check_tick_text(26, ['Midterm Exam = 0%'], 'Midterm')
            self._check_tick_text(27, ['Final Exam = 0%'], 'Final')

            self._check_tick_text(
                28,
                ['Homework = 0.75% of a possible 15.00%', 'Lab = 1.50% of a possible 15.00%'],
                'Total',
                False  # The label "Total" should NOT be aria-hidden
            )

            # The grading policy has 12 Homeworks and 12 Labs. Most of them are unpublished,
            # with no additional information.
            for i in range(1, 10):
                self._check_tick_text(
                    i,
                    [f'Homework {i + 1} Unreleased - 0% (?/?)'],
                    f'HW 0{i + 1}' if i < 9 else f'HW {i + 1}'
                )
                self._check_tick_text(
                    i + 13,
                    [f'Lab {i + 1} Unreleased - 0% (?/?)'],
                    f'Lab 0{i + 1}' if i < 9 else f'Lab {i + 1}'
                )

            # Verify the overall score. The first element in the array is the sr-only text, and the
            # second is the total text (including the sr-only text).
            assert ['Overall Score', 'Overall Score\n2%'] == self.progress_page.graph_overall_score()


class ProgressPageA11yTest(ProgressPageBaseTest):
    """
    Class to test the accessibility of the progress page.
    """
    a11y = True

    def test_progress_page_a11y(self):
        """
        Test the accessibility of the progress page.
        """
        self.progress_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        self.progress_page.visit()
        self.progress_page.a11y_audit.check_for_accessibility_errors()
