"""
Code to manage fetching and storing the metadata of IdPs.
"""


import datetime
import logging

import dateutil.parser
import pytz
import requests
from celery import shared_task
from django.utils.timezone import now
from edx_django_utils.monitoring import set_code_owner_attribute
from lxml import etree
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from requests import exceptions

from openedx.core.djangolib.markup import Text
from common.djangoapps.third_party_auth.models import SAMLConfiguration, SAMLProviderConfig, SAMLProviderData

log = logging.getLogger(__name__)

SAML_XML_NS = 'urn:oasis:names:tc:SAML:2.0:metadata'  # The SAML Metadata XML namespace


class MetadataParseError(Exception):
    """ An error occurred while parsing the SAML metadata from an IdP """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


@shared_task
@set_code_owner_attribute
def fetch_saml_metadata():
    """
    Fetch and store/update the metadata of all IdPs

    This task should be run on a daily basis.
    It's OK to run this whether or not SAML is enabled.

    Return value:
        tuple(num_skipped, num_attempted, num_updated, num_failed, failure_messages)
        num_total: Total number of providers found in the database
        num_skipped: Number of providers skipped for various reasons (see L52)
        num_attempted: Number of providers whose metadata was fetched
        num_updated: Number of providers that are either new or whose metadata has changed
        num_failed: Number of providers that could not be updated
        failure_messages: List of error messages for the providers that could not be updated
    """

    # First make a list of all the metadata XML URLs:
    saml_providers = SAMLProviderConfig.key_values('slug', flat=True)
    num_total = len(saml_providers)
    num_skipped = 0
    url_map = {}
    for idp_slug in saml_providers:
        config = SAMLProviderConfig.current(idp_slug)
        saml_config_slug = config.saml_configuration.slug if config.saml_configuration else 'default'

        # Skip SAML provider configurations which do not qualify for fetching
        if any([
            not config.enabled,
            not config.automatic_refresh_enabled,
            not SAMLConfiguration.is_enabled(config.site, saml_config_slug)
        ]):
            num_skipped += 1
            continue

        url = config.metadata_source
        if url not in url_map:
            url_map[url] = []
        if config.entity_id not in url_map[url]:
            url_map[url].append(config.entity_id)

    # Now attempt to fetch the metadata for the remaining SAML providers:
    num_attempted = len(url_map)
    num_updated = 0
    failure_messages = []  # We return the length of this array for num_failed
    for url, entity_ids in url_map.items():
        try:
            log.info("Fetching %s", url)
            if not url.lower().startswith('https'):
                log.warning("This SAML metadata URL is not secure! It should use HTTPS. (%s)", url)
            response = requests.get(url, verify=True)  # May raise HTTPError or SSLError or ConnectionError
            response.raise_for_status()  # May raise an HTTPError

            try:
                parser = etree.XMLParser(remove_comments=True)
                xml = etree.fromstring(response.content, parser)
            except etree.XMLSyntaxError:  # lint-amnesty, pylint: disable=try-except-raise
                raise
            # TODO: Can use OneLogin_Saml2_Utils to validate signed XML if anyone is using that

            for entity_id in entity_ids:
                log.info("Processing IdP with entityID %s", entity_id)
                public_key, sso_url, expires_at = _parse_metadata_xml(xml, entity_id)
                changed = _update_data(entity_id, public_key, sso_url, expires_at)
                if changed:
                    log.info("→ Created new record for SAMLProviderData")
                    num_updated += 1
                else:
                    log.info("→ Updated existing SAMLProviderData. Nothing has changed.")
        except (exceptions.SSLError, exceptions.HTTPError, exceptions.RequestException, MetadataParseError) as error:
            # Catch and process exception in case of errors during fetching and processing saml metadata.
            # Here is a description of each exception.
            # SSLError is raised in case of errors caused by SSL (e.g. SSL cer verification failure etc.)
            # HTTPError is raised in case of unexpected status code (e.g. 500 error etc.)
            # RequestException is the base exception for any request related error that "requests" lib raises.
            # MetadataParseError is raised if there is error in the fetched meta data (e.g. missing @entityID etc.)

            log.exception(str(error))
            failure_messages.append(
                "{error_type}: {error_message}\nMetadata Source: {url}\nEntity IDs: \n{entity_ids}.".format(
                    error_type=type(error).__name__,
                    error_message=str(error),
                    url=url,
                    entity_ids="\n".join(
                        [f"\t{count}: {item}" for count, item in enumerate(entity_ids, start=1)],
                    )
                )
            )
        except etree.XMLSyntaxError as error:
            log.exception(str(error))
            failure_messages.append(
                "XMLSyntaxError: {error_message}\nMetadata Source: {url}\nEntity IDs: \n{entity_ids}.".format(
                    error_message=str(error.error_log),  # lint-amnesty, pylint: disable=no-member
                    url=url,
                    entity_ids="\n".join(
                        [f"\t{count}: {item}" for count, item in enumerate(entity_ids, start=1)],
                    )
                )
            )

    # Return counts for total, skipped, attempted, updated, and failed, along with any failure messages
    return num_total, num_skipped, num_attempted, num_updated, len(failure_messages), failure_messages


def _parse_metadata_xml(xml, entity_id):
    """
    Given an XML document containing SAML 2.0 metadata, parse it and return a tuple of
    (public_key, sso_url, expires_at) for the specified entityID.

    Raises MetadataParseError if anything is wrong.
    """
    if xml.tag == etree.QName(SAML_XML_NS, 'EntityDescriptor'):
        entity_desc = xml
    else:
        if xml.tag != etree.QName(SAML_XML_NS, 'EntitiesDescriptor'):
            raise MetadataParseError(Text("Expected root element to be <EntitiesDescriptor>, not {}").format(xml.tag))
        entity_desc = xml.find(
            ".//{}[@entityID='{}']".format(etree.QName(SAML_XML_NS, 'EntityDescriptor'), entity_id)
        )
        if entity_desc is None:
            raise MetadataParseError(f"Can't find EntityDescriptor for entityID {entity_id}")

    expires_at = None
    if "validUntil" in xml.attrib:
        expires_at = dateutil.parser.parse(xml.attrib["validUntil"])
    if "cacheDuration" in xml.attrib:
        cache_expires = OneLogin_Saml2_Utils.parse_duration(xml.attrib["cacheDuration"])
        cache_expires = datetime.datetime.fromtimestamp(cache_expires, tz=pytz.utc)
        if expires_at is None or cache_expires < expires_at:
            expires_at = cache_expires

    sso_desc = entity_desc.find(etree.QName(SAML_XML_NS, "IDPSSODescriptor"))
    if sso_desc is None:
        raise MetadataParseError("IDPSSODescriptor missing")
    if 'urn:oasis:names:tc:SAML:2.0:protocol' not in sso_desc.get("protocolSupportEnumeration"):
        raise MetadataParseError("This IdP does not support SAML 2.0")

    # Now we just need to get the public_key and sso_url
    public_key = sso_desc.findtext("./{}//{}".format(
        etree.QName(SAML_XML_NS, "KeyDescriptor"), "{http://www.w3.org/2000/09/xmldsig#}X509Certificate"
    ))
    if not public_key:
        raise MetadataParseError("Public Key missing. Expected an <X509Certificate>")
    public_key = public_key.replace(" ", "")
    binding_elements = sso_desc.iterfind("./{}".format(etree.QName(SAML_XML_NS, "SingleSignOnService")))
    sso_bindings = {element.get('Binding'): element.get('Location') for element in binding_elements}
    try:
        # The only binding supported by python-saml and python-social-auth is HTTP-Redirect:
        sso_url = sso_bindings['urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect']
    except KeyError:
        raise MetadataParseError("Unable to find SSO URL with HTTP-Redirect binding.")  # lint-amnesty, pylint: disable=raise-missing-from
    return public_key, sso_url, expires_at


def _update_data(entity_id, public_key, sso_url, expires_at):
    """
    Update/Create the SAMLProviderData for the given entity ID.
    Return value:
        False if nothing has changed and existing data's "fetched at" timestamp is just updated.
        True if a new record was created. (Either this is a new provider or something changed.)
    """
    data_obj = SAMLProviderData.current(entity_id)
    fetched_at = now()
    if data_obj and (data_obj.public_key == public_key and data_obj.sso_url == sso_url):
        data_obj.expires_at = expires_at
        data_obj.fetched_at = fetched_at
        data_obj.save()
        return False
    else:
        SAMLProviderData.objects.create(
            entity_id=entity_id,
            fetched_at=fetched_at,
            expires_at=expires_at,
            sso_url=sso_url,
            public_key=public_key,
        )
        return True
