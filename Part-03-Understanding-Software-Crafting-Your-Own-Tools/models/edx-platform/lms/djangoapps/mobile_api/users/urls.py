"""
URLs for user API
"""


from django.conf import settings
from django.conf.urls import url

from .views import UserCourseEnrollmentsList, UserCourseStatus, UserDetail

urlpatterns = [
    url('^' + settings.USERNAME_PATTERN + '$', UserDetail.as_view(), name='user-detail'),
    url(
        '^' + settings.USERNAME_PATTERN + '/course_enrollments/$',
        UserCourseEnrollmentsList.as_view(),
        name='courseenrollment-detail'
    ),
    url(f'^{settings.USERNAME_PATTERN}/course_status_info/{settings.COURSE_ID_PATTERN}',
        UserCourseStatus.as_view(),
        name='user-course-status')
]
