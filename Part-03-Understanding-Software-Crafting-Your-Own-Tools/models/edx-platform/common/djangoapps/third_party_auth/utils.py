"""
Utility functions for third_party_auth
"""

from uuid import UUID
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from enterprise.models import EnterpriseCustomerUser, EnterpriseCustomerIdentityProvider
from social_core.pipeline.social_auth import associate_by_email

from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
from . import provider


def user_exists(details):
    """
    Return True if user with given details exist in the system.

    Arguments:
        details (dict): dictionary containing user infor like email, username etc.

    Returns:
        (bool): True if user with given details exists, `False` otherwise.
    """
    user_queryset_filter = {}
    email = details.get('email')
    username = details.get('username')
    if email:
        user_queryset_filter['email'] = email
    elif username:
        user_queryset_filter['username__iexact'] = username

    if user_queryset_filter:
        return User.objects.filter(**user_queryset_filter).exists()

    return False


def get_user_from_email(details):
    """
    Return user with given details exist in the system.∂i

    Arguments:
        details (dict): dictionary containing user email.

    Returns:
        User: if user with given details exists, None otherwise.
    """
    email = details.get('email')
    if email:
        return User.objects.filter(email=email).first()

    return None


def convert_saml_slug_provider_id(provider):  # lint-amnesty, pylint: disable=redefined-outer-name
    """
    Provider id is stored with the backend type prefixed to it (ie "saml-")
    Slug is stored without this prefix.
    This just converts between them whenever you expect the opposite of what you currently have.

    Arguments:
        provider (string): provider_id or slug

    Returns:
        (string): Opposite of what you inputted (slug -> provider_id; provider_id -> slug)
    """
    if provider.startswith('saml-'):
        return provider[5:]
    else:
        return 'saml-' + provider


def validate_uuid4_string(uuid_string):
    """
    Returns True if valid uuid4 string, or False
    """
    try:
        UUID(uuid_string, version=4)
    except ValueError:
        return False
    return True


def is_saml_provider(backend, kwargs):
    """ Verify that the third party provider uses SAML """
    current_provider = provider.Registry.get_from_pipeline({'backend': backend, 'kwargs': kwargs})
    saml_providers_list = list(provider.Registry.get_enabled_by_backend_name('tpa-saml'))
    return (current_provider and
            current_provider.slug in [saml_provider.slug for saml_provider in saml_providers_list]), current_provider


def is_enterprise_customer_user(provider_id, user):
    """ Verify that the user linked to enterprise customer of current identity provider"""
    enterprise_idp = EnterpriseCustomerIdentityProvider.objects.get(provider_id=provider_id)

    return EnterpriseCustomerUser.objects.filter(enterprise_customer=enterprise_idp.enterprise_customer,
                                                 user_id=user.id).exists()


def is_oauth_provider(backend_name, **kwargs):
    """
    Verify that the third party provider uses oauth
    """
    current_provider = provider.Registry.get_from_pipeline({'backend': backend_name, 'kwargs': kwargs})
    if current_provider:
        return current_provider.provider_id.startswith(OAuth2ProviderConfig.prefix)

    return False


def get_associated_user_by_email_response(backend, details, user, *args, **kwargs):
    """
    Gets the user associated by the `associate_by_email` social auth method
    """

    association_response = associate_by_email(backend, details, user, *args, **kwargs)

    if (
        association_response and
        association_response.get('user')
    ):
        # Only return the user matched by email if their email has been activated.
        # Otherwise, an illegitimate user can create an account with another user's
        # email address and the legitimate user would now login to the illegitimate
        # account.
        return (association_response, association_response['user'].is_active)

    return (None, False)
