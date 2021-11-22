"""
Unit tests for the VerificationDeadline signals
"""


from datetime import timedelta

from django.utils.timezone import now
from unittest.mock import patch

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification, VerificationDeadline
from lms.djangoapps.verify_student.signals import _listen_for_course_publish, _listen_for_lms_retire
from lms.djangoapps.verify_student.tests.factories import SoftwareSecurePhotoVerificationFactory
from openedx.core.djangoapps.user_api.accounts.tests.retirement_helpers import fake_completed_retirement
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class VerificationDeadlineSignalTest(ModuleStoreTestCase):
    """
    Tests for the VerificationDeadline signal
    """

    def setUp(self):
        super().setUp()
        self.end = now().replace(microsecond=0) + timedelta(days=7)
        self.course = CourseFactory.create(end=self.end)
        VerificationDeadline.objects.all().delete()

    def test_no_deadline(self):
        """ Verify the signal sets deadline to course end when no deadline exists."""
        _listen_for_course_publish('store', self.course.id)

        assert VerificationDeadline.deadline_for_course(self.course.id) == self.course.end

    def test_deadline(self):
        """ Verify deadline is set to course end date by signal when changed. """
        deadline = now() - timedelta(days=7)
        VerificationDeadline.set_deadline(self.course.id, deadline)

        _listen_for_course_publish('store', self.course.id)
        assert VerificationDeadline.deadline_for_course(self.course.id) == self.course.end

    def test_deadline_explicit(self):
        """ Verify deadline is unchanged by signal when explicitly set. """
        deadline = now() - timedelta(days=7)
        VerificationDeadline.set_deadline(self.course.id, deadline, is_explicit=True)

        _listen_for_course_publish('store', self.course.id)

        actual_deadline = VerificationDeadline.deadline_for_course(self.course.id)
        assert actual_deadline != self.course.end
        assert actual_deadline == deadline


class RetirementSignalTest(ModuleStoreTestCase):
    """
    Tests for the VerificationDeadline signal
    """

    def _create_entry(self):
        """
        Helper method to create and return a SoftwareSecurePhotoVerification with appropriate data
        """
        name = 'Test Name'
        face_url = 'https://test.invalid'
        id_url = 'https://test2.invalid'
        key = 'test+key'
        user = UserFactory()
        return SoftwareSecurePhotoVerificationFactory(
            user=user,
            name=name,
            face_image_url=face_url,
            photo_id_image_url=id_url,
            photo_id_key=key
        )

    def test_retire_success(self):
        verification = self._create_entry()
        _listen_for_lms_retire(sender=self.__class__, user=verification.user)

        ver_obj = SoftwareSecurePhotoVerification.objects.get(user=verification.user)

        # All values for this user should now be empty string
        for field in ('name', 'face_image_url', 'photo_id_image_url', 'photo_id_key'):
            assert '' == getattr(ver_obj, field)

    def test_retire_success_no_entries(self):
        user = UserFactory()
        _listen_for_lms_retire(sender=self.__class__, user=user)

    def test_idempotent(self):
        verification = self._create_entry()

        # Run this twice to make sure there are no errors raised 2nd time through
        _listen_for_lms_retire(sender=self.__class__, user=verification.user)
        fake_completed_retirement(verification.user)
        _listen_for_lms_retire(sender=self.__class__, user=verification.user)

        ver_obj = SoftwareSecurePhotoVerification.objects.get(user=verification.user)

        # All values for this user should now be empty string
        for field in ('name', 'face_image_url', 'photo_id_image_url', 'photo_id_key'):
            assert '' == getattr(ver_obj, field)


class PostSavePhotoVerificationTest(ModuleStoreTestCase):
    """
    Tests for the post_save signal on the SoftwareSecurePhotoVerification model.
    This receiver should emit another signal that contains limited data about
    the verification attempt that was updated.
    """

    @patch('lms.djangoapps.verify_student.signals.idv_update_signal.send')
    def test_post_save_signal(self, mock_signal):
        user = UserFactory.create()

        # create new softwaresecureverification
        attempt = SoftwareSecurePhotoVerification.objects.create(
            user=user,
            name='Bob Doe',
            face_image_url='https://test.face',
            photo_id_image_url='https://test.photo',
            photo_id_key='test+key'
        )
        self.assertTrue(mock_signal.called)
        mock_signal.assert_called_with(
            sender='idv_update',
            attempt_id=attempt.id,
            user_id=attempt.user.id,
            status=attempt.status,
            full_name=attempt.name,
            profile_name=attempt.user.profile.name
        )
        mock_signal.reset_mock()

        attempt.mark_ready()

        self.assertTrue(mock_signal.called)
        mock_signal.assert_called_with(
            sender='idv_update',
            attempt_id=attempt.id,
            user_id=attempt.user.id,
            status=attempt.status,
            full_name=attempt.name,
            profile_name=attempt.user.profile.name
        )
