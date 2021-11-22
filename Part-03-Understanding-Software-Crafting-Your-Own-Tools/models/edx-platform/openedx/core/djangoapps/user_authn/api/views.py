"""
Authn API Views
"""

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser

from common.djangoapps.student.helpers import get_next_url_for_login_page
from openedx.core.djangoapps.user_authn.views.utils import get_mfe_context
from common.djangoapps.student.views import compose_and_send_activation_email


class MFEContextThrottle(AnonRateThrottle):
    """
    Setting rate limit for MFEContextView API
    """
    rate = settings.LOGISTRATION_API_RATELIMIT


class MFEContextView(APIView):
    """
    API to get third party auth providers, user country code and the currently running pipeline.
    """
    throttle_classes = [MFEContextThrottle]

    def get(self, request, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """
        Returns the context for third party auth providers, user country code
        and the currently running pipeline.

        Arguments:
            request (HttpRequest): The request, used to determine if a pipeline
                is currently running.
            tpa_hint (string): An override flag that will return a matching provider
                as long as its configuration has been enabled
        """
        request_params = request.GET
        redirect_to = get_next_url_for_login_page(request)
        third_party_auth_hint = request_params.get('tpa_hint')

        context = get_mfe_context(request, redirect_to, third_party_auth_hint)
        return Response(
            status=status.HTTP_200_OK,
            data=context
        )


class SendAccountActivationEmail(APIView):
    """
    API to to send the account activation email using account activation cta.
    """
    authentication_classes = (SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """
        Returns status code.
        Arguments:
            request (HttpRequest): The request, used to get the user
        """
        try:
            user = request.user
            if not user.is_active:
                compose_and_send_activation_email(user, user.profile)
            return Response(
                status=status.HTTP_200_OK
            )
        except Exception:  # pylint: disable=broad-except
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
