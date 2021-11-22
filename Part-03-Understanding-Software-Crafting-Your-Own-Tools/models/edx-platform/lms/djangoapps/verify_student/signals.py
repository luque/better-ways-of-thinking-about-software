"""
Signal handler for setting default course verification dates
"""


from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import Signal
from django.dispatch.dispatcher import receiver

from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_LMS_CRITICAL
from xmodule.modulestore.django import SignalHandler, modulestore

from .models import SoftwareSecurePhotoVerification, VerificationDeadline


# Signal for emitting IDV submission and review updates
idv_update_signal = Signal(providing_args=["attempt_id", "user_id", "status", "full_name", "profile_name"])


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    sets the verification deadline date to a default.
    """
    course = modulestore().get_course(course_key)
    if course:
        try:
            deadline = VerificationDeadline.objects.get(course_key=course_key)
            if not deadline.deadline_is_explicit and deadline.deadline != course.end:
                VerificationDeadline.set_deadline(course_key, course.end)
        except ObjectDoesNotExist:
            VerificationDeadline.set_deadline(course_key, course.end)


@receiver(USER_RETIRE_LMS_CRITICAL)
def _listen_for_lms_retire(sender, **kwargs):  # pylint: disable=unused-argument
    user = kwargs.get('user')
    SoftwareSecurePhotoVerification.retire_user(user.id)


@receiver(post_save, sender=SoftwareSecurePhotoVerification)
def send_idv_update(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the post save signal from the SoftwareSecurePhotoVerification model, and emits
    another signal with limited information from the model. We are choosing to re-emit a signal
    as opposed to relying only on the post_save signal to avoid the chance that other apps
    import the SoftwareSecurePhotoVerification model.
    """
    idv_update_signal.send(
        sender='idv_update',
        attempt_id=instance.id,
        user_id=instance.user.id,
        status=instance.status,
        full_name=instance.name,
        profile_name=instance.user.profile.name
    )
