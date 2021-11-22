"""
Extra utilities for waffle: most classes are defined in edx_toggles.toggles (https://edx-toggles.readthedocs.io/), but
we keep here some extra classes for usage within edx-platform. These classes cover course override use cases.
"""
import logging
import warnings
from contextlib import contextmanager

from edx_django_utils.monitoring import set_custom_attribute
from edx_toggles.toggles import (
    LegacyWaffleFlag,
    LegacyWaffleFlagNamespace,
    LegacyWaffleSwitch,
    LegacyWaffleSwitchNamespace,
)
from opaque_keys.edx.keys import CourseKey

log = logging.getLogger(__name__)


class CourseWaffleFlag(LegacyWaffleFlag):
    """
    Represents a single waffle flag that can be forced on/off for a course. This class should be used instead of
    WaffleFlag when in the context of a course.

    Uses a cached waffle namespace.

    Usage:

       SOME_COURSE_FLAG = CourseWaffleFlag('my_namespace', 'some_course_feature', __name__)

    And then we can check this flag in code with::

        SOME_COURSE_FLAG.is_enabled(course_key)

    To configure, go to "Waffle flag course overrides" under the Django Admin "waffle_utils" section.

        Waffle flag: Set this to the flag name (e.g. my_namespace.some_course_feature).
        Course id: Set this to the course id (e.g. course-v1:edx+100+Demo)
        Override choice: (Force on/Force off). "Force on" will enable the waffle flag for all users in a course,
            overriding any behavior configured on the waffle flag itself. "Force off" will disable the waffle flag
            for all users in a course, overriding any behavior configured on the waffle flag itself. Requires
            "Enabled" (see below) to apply.
        Enabled: This must be marked as enabled in order for the override to be applied. These settings can't be
            deleted, so instead, you need to disable if it should no longer apply.

    """

    def _get_course_override_value(self, course_key):
        """
        Returns True/False if the flag was forced on or off for the provided course. Returns None if the flag was not
        overridden.

        Note: Has side effect of caching the override value.

        Arguments:
            course_key (CourseKey): The course to check for override before checking waffle.
        """
        # Import is placed here to avoid model import at project startup.
        from .models import WaffleFlagCourseOverrideModel

        cache_key = f"{self.name}.{str(course_key)}"
        course_override = self.cached_flags().get(cache_key)

        if course_override is None:
            course_override = WaffleFlagCourseOverrideModel.override_value(
                self.name, course_key
            )
            self.cached_flags()[cache_key] = course_override

        if course_override == WaffleFlagCourseOverrideModel.ALL_CHOICES.on:
            return True
        if course_override == WaffleFlagCourseOverrideModel.ALL_CHOICES.off:
            return False
        return None

    def is_enabled(self, course_key=None):  # pylint: disable=arguments-differ
        """
        Returns whether or not the flag is enabled within the context of a given course.

        Arguments:
            course_key (Optional[CourseKey]): The course to check for override before
                checking waffle. If omitted, check whether the flag is enabled
                outside the context of any course.
        """
        if course_key:
            assert isinstance(
                course_key, CourseKey
            ), "Provided course_key '{}' is not instance of CourseKey.".format(
                course_key
            )
        is_enabled_for_course = self._get_course_override_value(course_key)
        if is_enabled_for_course is not None:
            return is_enabled_for_course
        return super().is_enabled()
