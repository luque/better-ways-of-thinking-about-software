"""
Django admin commands related to verify_student
"""


import logging
import os
from pprint import pformat

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.management.base import BaseCommand, CommandError

from lms.djangoapps.verify_student.models import ManualVerification
from lms.djangoapps.verify_student.utils import earliest_allowed_verification_date

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This method attempts to manually verify users.
    Example usage:
        $ ./manage.py lms manual_verifications --email-ids-file <absolute path of file with email ids (one per line)>
    """
    help = 'Manually verifies one or more users passed as an argument list.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email-ids-file',
            action='store',
            dest='email_ids_file',
            default=None,
            help='Path of the file to read email id from.',
            type=str,
        )
        parser.add_argument(
            '--email',
            default=None,
            help='Single email to verify one user',
            type=str,
        )

    def handle(self, *args, **options):

        single_email = options['email']

        if single_email:
            successfully_verified = self._add_user_to_manual_verification(single_email)
            if successfully_verified is False:
                log.error(f'Manual verification of {single_email} failed')
            return

        email_ids_file = options['email_ids_file']

        if email_ids_file:
            if not os.path.exists(email_ids_file):
                raise CommandError('Pass the correct absolute path to email ids file as --email-ids-file argument.')

        total_emails, failed_emails = self._generate_manual_verification_from_file(email_ids_file)

        if failed_emails:
            log.error('Completed manual verification. {} of {} failed.'.format(
                len(failed_emails),
                total_emails
            ))
            log.error(f'Failed emails:{pformat(failed_emails)}')
        else:
            log.info(f'Successfully generated manual verification for {total_emails} emails.')

    def _generate_manual_verification_from_file(self, email_ids_file):
        """
        Generate manual verification for the emails provided in the email ids file.

        Arguments:
            email_ids_file (str): path of the file containing email ids.

        Returns:
            (total_emails, failed_emails): a tuple containing count of emails processed and a list containing
             emails whose verifications could not be processed.
        """
        failed_emails = []

        with open(email_ids_file) as file_handler:
            email_ids = file_handler.readlines()
            total_emails = len(email_ids)
            log.info(f'Creating manual verification for {total_emails} emails.')
            for email_id in email_ids:
                successfully_verified = self._add_user_to_manual_verification(email_id)
                if successfully_verified is False:
                    failed_emails.append(email_id)
        return total_emails, failed_emails

    def _add_user_to_manual_verification(self, email_id):
        """
        Generates a single verification for a user.

        Arguments:
            email_id (str): email of the user to be verified

        Returns:
            (success): boolean to show if the user has been successfully verified.
        """
        try:
            email_id = email_id.strip()
            user = User.objects.get(email=email_id)
            ManualVerification.objects.get_or_create(
                user=user,
                status='approved',
                created_at__gte=earliest_allowed_verification_date(),
                defaults={'name': user.profile.name},
            )
            return True
        except User.DoesNotExist:
            log.error(f'Tried to verify email {email_id}, but user not found')
            return False
