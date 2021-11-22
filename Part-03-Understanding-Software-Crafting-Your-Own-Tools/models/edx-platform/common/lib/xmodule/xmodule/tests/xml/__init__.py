"""
Xml parsing tests for XModules
"""


import pprint
from unittest.mock import Mock

from django.test import TestCase
from lxml import etree
from opaque_keys.edx.keys import CourseKey
from xblock.runtime import DictKeyValueStore, KvsFieldData

from xmodule.mako_module import MakoDescriptorSystem
from xmodule.modulestore.xml import CourseLocationManager
from xmodule.x_module import XMLParsingSystem, policy_key


class InMemorySystem(XMLParsingSystem, MakoDescriptorSystem):  # pylint: disable=abstract-method
    """
    The simplest possible XMLParsingSystem
    """
    def __init__(self, xml_import_data):
        self.course_id = CourseKey.from_string(xml_import_data.course_id)
        self.default_class = xml_import_data.default_class
        self._descriptors = {}

        def get_policy(usage_id):
            """Return the policy data for the specified usage"""
            return xml_import_data.policy.get(policy_key(usage_id), {})

        super().__init__(
            get_policy=get_policy,
            process_xml=self.process_xml,
            load_item=self.load_item,
            error_tracker=Mock(),
            resources_fs=xml_import_data.filesystem,
            mixins=xml_import_data.xblock_mixins,
            select=xml_import_data.xblock_select,
            render_template=lambda template, context: pprint.pformat((template, context)),
            field_data=KvsFieldData(DictKeyValueStore()),
        )

    def process_xml(self, xml):  # pylint: disable=method-hidden
        """Parse `xml` as an XBlock, and add it to `self._descriptors`"""
        self.get_asides = Mock(return_value=[])
        descriptor = self.xblock_from_node(
            etree.fromstring(xml),
            None,
            CourseLocationManager(self.course_id),
        )
        self._descriptors[str(descriptor.location)] = descriptor
        return descriptor

    def load_item(self, location, for_parent=None):  # pylint: disable=method-hidden, unused-argument
        """Return the descriptor loaded for `location`"""
        return self._descriptors[str(location)]


class XModuleXmlImportTest(TestCase):
    """Base class for tests that use basic XML parsing"""
    @classmethod
    def process_xml(cls, xml_import_data):
        """Use the `xml_import_data` to import an :class:`XBlock` from XML."""
        system = InMemorySystem(xml_import_data)
        return system.process_xml(xml_import_data.xml_string)
