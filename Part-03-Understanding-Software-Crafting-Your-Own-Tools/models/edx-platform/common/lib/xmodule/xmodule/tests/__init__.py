"""
unittests for xmodule

Run like this:

    paver test_lib -l common/lib/xmodule

"""


import inspect
import json
import os
import pprint
import sys
import traceback
import unittest
from contextlib import contextmanager
from functools import wraps
from unittest.mock import Mock

from django.test import TestCase

from opaque_keys.edx.keys import CourseKey
from path import Path as path
from xblock.core import XBlock
from xblock.field_data import DictFieldData
from xblock.fields import Reference, ReferenceList, ReferenceValueDict, ScopeIds

from xmodule.assetstore import AssetMetadata
from xmodule.error_module import ErrorBlock
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.draft_and_published import ModuleStoreDraftAndPublished
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.xml import CourseLocationManager
from xmodule.x_module import ModuleSystem, XModuleDescriptor, XModuleMixin

MODULE_DIR = path(__file__).dirname()
# Location of common test DATA directory
# '../../../../edx-platform/common/test/data/'
DATA_DIR = MODULE_DIR.parent.parent.parent.parent / "test" / "data"


class TestModuleSystem(ModuleSystem):  # pylint: disable=abstract-method
    """
    ModuleSystem for testing
    """
    def __init__(self, **kwargs):
        id_manager = CourseLocationManager(kwargs['course_id'])
        kwargs.setdefault('id_reader', id_manager)
        kwargs.setdefault('id_generator', id_manager)
        kwargs.setdefault('services', {}).setdefault('field-data', DictFieldData({}))
        super().__init__(**kwargs)

    def handler_url(self, block, handler, suffix='', query='', thirdparty=False):  # lint-amnesty, pylint: disable=arguments-differ
        return '{usage_id}/{handler}{suffix}?{query}'.format(
            usage_id=str(block.scope_ids.usage_id),
            handler=handler,
            suffix=suffix,
            query=query,
        )

    def local_resource_url(self, block, uri):
        return 'resource/{usage_id}/{uri}'.format(
            usage_id=str(block.scope_ids.usage_id),
            uri=uri,
        )

    # Disable XBlockAsides in most tests
    def get_asides(self, block):
        return []

    def __repr__(self):
        """
        Custom hacky repr.
        XBlock.Runtime.render() replaces the _view_name attribute while rendering, which
        causes rendered comparisons of blocks to fail as unequal. So make the _view_name
        attribute None during the base repr - and set it back to original value afterward.
        """
        orig_view_name = None
        if hasattr(self, '_view_name'):
            orig_view_name = self._view_name
        self._view_name = None
        rt_repr = super().__repr__()
        self._view_name = orig_view_name
        return rt_repr


def get_test_system(
    course_id=CourseKey.from_string('/'.join(['org', 'course', 'run'])),
    user=None,
):
    """
    Construct a test ModuleSystem instance.

    By default, the render_template() method simply returns the repr of the
    context it is passed.  You can override this behavior by monkey patching::

        system = get_test_system()
        system.render_template = my_render_func

    where `my_render_func` is a function of the form my_render_func(template, context).

    """
    if not user:
        user = Mock(name='get_test_system.user', is_staff=False)

    descriptor_system = get_test_descriptor_system()

    def get_module(descriptor):
        """Mocks module_system get_module function"""

        # Unlike XBlock Runtimes or DescriptorSystems,
        # each XModule is provided with a new ModuleSystem.
        # Construct one for the new XModule.
        module_system = get_test_system()

        # Descriptors can all share a single DescriptorSystem.
        # So, bind to the same one as the current descriptor.
        module_system.descriptor_runtime = descriptor._runtime  # pylint: disable=protected-access

        descriptor.bind_for_student(module_system, user.id)

        return descriptor

    return TestModuleSystem(
        static_url='/static',
        track_function=Mock(name='get_test_system.track_function'),
        get_module=get_module,
        render_template=mock_render_template,
        replace_urls=str,
        user=user,
        get_real_user=lambda __: user,
        filestore=Mock(name='get_test_system.filestore', root_path='.'),
        debug=True,
        hostname="edx.org",
        xqueue={
            'interface': None,
            'callback_url': '/',
            'default_queuename': 'testqueue',
            'waittime': 10,
            'construct_callback': Mock(name='get_test_system.xqueue.construct_callback', side_effect="/"),
        },
        node_path=os.environ.get("NODE_PATH", "/usr/local/lib/node_modules"),
        anonymous_student_id='student',
        course_id=course_id,
        error_descriptor_class=ErrorBlock,
        get_user_role=Mock(name='get_test_system.get_user_role', is_staff=False),
        user_location=Mock(name='get_test_system.user_location'),
        descriptor_runtime=descriptor_system,
    )


def get_test_descriptor_system():
    """
    Construct a test DescriptorSystem instance.
    """
    field_data = DictFieldData({})

    descriptor_system = MakoDescriptorSystem(
        load_item=Mock(name='get_test_descriptor_system.load_item'),
        resources_fs=Mock(name='get_test_descriptor_system.resources_fs'),
        error_tracker=Mock(name='get_test_descriptor_system.error_tracker'),
        render_template=mock_render_template,
        mixins=(InheritanceMixin, XModuleMixin),
        field_data=field_data,
        services={'field-data': field_data},
    )
    descriptor_system.get_asides = lambda block: []
    return descriptor_system


def mock_render_template(*args, **kwargs):
    """
    Pretty-print the args and kwargs.

    Allows us to not depend on any actual template rendering mechanism,
    while still returning a unicode object
    """
    return pprint.pformat((args, kwargs)).encode().decode()


class ModelsTest(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def test_load_class(self):
        vc = XBlock.load_class('sequential')
        vc_str = "<class 'xmodule.seq_module.SequenceBlock'>"
        assert str(vc) == vc_str


def map_references(value, field, actual_course_key):
    """
    Map the references in value to actual_course_key and return value
    """
    if not value:  # if falsey
        return value
    if isinstance(field, Reference):
        return value.map_into_course(actual_course_key)
    if isinstance(field, ReferenceList):
        return [sub.map_into_course(actual_course_key) for sub in value]
    if isinstance(field, ReferenceValueDict):
        return {key: ele.map_into_course(actual_course_key) for key, ele in value.items()}
    return value


class LazyFormat:
    """
    An stringy object that delays formatting until it's put into a string context.
    """
    __slots__ = ('template', 'args', 'kwargs', '_message')

    def __init__(self, template, *args, **kwargs):
        self.template = template
        self.args = args
        self.kwargs = kwargs
        self._message = None

    def __str__(self):
        if self._message is None:
            self._message = self.template.format(*self.args, **self.kwargs)
        return self._message

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(str(self))

    def __getitem__(self, index):
        return str(self)[index]


class CourseComparisonTest(TestCase):
    """
    Mixin that has methods for comparing courses for equality.
    """

    def setUp(self):
        super().setUp()
        self.field_exclusions = set()
        self.ignored_asset_keys = set()

    def exclude_field(self, usage_id, field_name):
        """
        Mark field ``field_name`` of expected block usage ``usage_id`` as ignored

        Args:
            usage_id (:class:`opaque_keys.edx.UsageKey` or ``None``). If ``None``, skip, this field in all blocks
            field_name (string): The name of the field to skip
        """
        self.field_exclusions.add((usage_id, field_name))

    def ignore_asset_key(self, key_name):
        """
        Add an asset key to the list of keys to be ignored when comparing assets.

        Args:
            key_name: The name of the key to ignore.
        """
        self.ignored_asset_keys.add(key_name)

    def assertReferenceRelativelyEqual(self, reference_field, expected_block, actual_block):
        """
        Assert that the supplied reference field is identical on the expected_block and actual_block,
        assoming that the references are only relative (that is, comparing only on block_type and block_id,
        not course_key).
        """
        def extract_key(usage_key):
            if usage_key is None:
                return None
            else:
                return (usage_key.block_type, usage_key.block_id)
        expected = reference_field.read_from(expected_block)
        actual = reference_field.read_from(actual_block)
        if isinstance(reference_field, Reference):
            expected = extract_key(expected)
            actual = extract_key(actual)
        elif isinstance(reference_field, ReferenceList):
            expected = [extract_key(key) for key in expected]
            actual = [extract_key(key) for key in actual]
        elif isinstance(reference_field, ReferenceValueDict):
            expected = {key: extract_key(val) for (key, val) in expected.items()}
            actual = {key: extract_key(val) for (key, val) in actual.items()}
        assert expected == actual,\
            LazyFormat("Field {} doesn't match between usages {} and {}: {!r} != {!r}",
                       reference_field.name,
                       expected_block.scope_ids.usage_id,
                       actual_block.scope_ids.usage_id,
                       expected, actual)

    def assertBlocksEqualByFields(self, expected_block, actual_block):
        """
        Compare block fields to check for equivalence.
        """
        assert expected_block.fields == actual_block.fields
        for field in expected_block.fields.values():
            self.assertFieldEqual(field, expected_block, actual_block)

    def assertFieldEqual(self, field, expected_block, actual_block):
        """
        Compare a single block field for equivalence.
        """
        if isinstance(field, (Reference, ReferenceList, ReferenceValueDict)):
            self.assertReferenceRelativelyEqual(field, expected_block, actual_block)
        else:
            expected = field.read_from(expected_block)
            actual = field.read_from(actual_block)
            assert expected == actual,\
                LazyFormat("Field {} doesn't match between usages {} and {}: {!r} != {!r}",
                           field.name,
                           expected_block.scope_ids.usage_id,
                           actual_block.scope_ids.usage_id,
                           expected, actual)

    def assertCoursesEqual(self, expected_store, expected_course_key, actual_store, actual_course_key):
        """
        Assert that the courses identified by ``expected_course_key`` in ``expected_store`` and
        ``actual_course_key`` in ``actual_store`` are identical (ignore differences related
        owing to the course_keys being different).

        Any field value mentioned in ``self.field_exclusions`` by the key (usage_id, field_name)
        will be ignored for the purpose of equality checking.
        """
        # compare published
        with expected_store.branch_setting(ModuleStoreEnum.Branch.published_only, expected_course_key):
            with actual_store.branch_setting(ModuleStoreEnum.Branch.published_only, actual_course_key):
                expected_items = expected_store.get_items(expected_course_key, revision=ModuleStoreEnum.RevisionOption.published_only)  # lint-amnesty, pylint: disable=line-too-long
                actual_items = actual_store.get_items(actual_course_key, revision=ModuleStoreEnum.RevisionOption.published_only)  # lint-amnesty, pylint: disable=line-too-long
                assert len(expected_items) > 0
                self._assertCoursesEqual(expected_items, actual_items, actual_course_key)

        # if the modulestore supports having a draft branch
        if isinstance(expected_store, ModuleStoreDraftAndPublished):
            with expected_store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, expected_course_key):
                with actual_store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, actual_course_key):
                    # compare draft
                    if expected_store.get_modulestore_type(None) == ModuleStoreEnum.Type.split:
                        revision = ModuleStoreEnum.RevisionOption.draft_only
                    else:
                        revision = None
                    expected_items = expected_store.get_items(expected_course_key, revision=revision)
                    if actual_store.get_modulestore_type(None) == ModuleStoreEnum.Type.split:
                        revision = ModuleStoreEnum.RevisionOption.draft_only
                    else:
                        revision = None
                    actual_items = actual_store.get_items(actual_course_key, revision=revision)
                    self._assertCoursesEqual(expected_items, actual_items, actual_course_key, expect_drafts=True)

    def _assertCoursesEqual(self, expected_items, actual_items, actual_course_key, expect_drafts=False):  # lint-amnesty, pylint: disable=unused-argument
        """
        Actual algorithm to compare courses.
        """

        assert len(expected_items) == len(actual_items)

        def map_key(usage_key):
            return (usage_key.block_type, usage_key.block_id)
        actual_item_map = {
            map_key(item.location): item
            for item in actual_items
        }
        # Split Mongo and Old-Mongo disagree about what the block_id of courses is, so skip those in
        # this comparison
        self.assertCountEqual(
            [map_key(item.location) for item in expected_items if item.scope_ids.block_type != 'course'],
            [key for key in actual_item_map.keys() if key[0] != 'course'],
        )
        for expected_item in expected_items:
            actual_item_location = actual_course_key.make_usage_key(expected_item.category, expected_item.location.block_id)  # lint-amnesty, pylint: disable=line-too-long
            # split and old mongo use different names for the course root but we don't know which
            # modulestore actual's come from here; so, assume old mongo and if that fails, assume split
            if expected_item.location.block_type == 'course':
                actual_item_location = actual_item_location.replace(name=actual_item_location.run)
            actual_item = actual_item_map.get(map_key(actual_item_location))
            # must be split
            if actual_item is None and expected_item.location.block_type == 'course':
                actual_item_location = actual_item_location.replace(name='course')
                actual_item = actual_item_map.get(map_key(actual_item_location))
            # Formatting the message slows down tests of large courses significantly, so only do it if it would be used
            assert map_key(actual_item_location) in list(actual_item_map.keys())
            if actual_item is None:
                continue
            # compare fields
            assert expected_item.fields == actual_item.fields
            for field_name, field in expected_item.fields.items():
                if (expected_item.scope_ids.usage_id, field_name) in self.field_exclusions:
                    continue
                if (None, field_name) in self.field_exclusions:
                    continue
                # Children are handled specially
                if field_name == 'children':
                    continue
                self.assertFieldEqual(field, expected_item, actual_item)
            # compare children
            assert expected_item.has_children == actual_item.has_children
            if expected_item.has_children:
                expected_children = [
                    (expected_item_child.location.block_type, expected_item_child.location.block_id)
                    # get_children() rather than children to strip privates from public parents
                    for expected_item_child in expected_item.get_children()
                ]
                actual_children = [
                    (item_child.location.block_type, item_child.location.block_id)
                    # get_children() rather than children to strip privates from public parents
                    for item_child in actual_item.get_children()
                ]
                assert expected_children == actual_children

    def assertAssetEqual(self, expected_course_key, expected_asset, actual_course_key, actual_asset):
        """
        Assert that two assets are equal, allowing for differences related to their being from different courses.
        """
        for key in self.ignored_asset_keys:
            if key in expected_asset:
                del expected_asset[key]
            if key in actual_asset:
                del actual_asset[key]

        expected_key = expected_asset.pop('asset_key')
        actual_key = actual_asset.pop('asset_key')
        assert expected_key.map_into_course(actual_course_key) == actual_key
        assert expected_key == actual_key.map_into_course(expected_course_key)

        expected_filename = expected_asset.pop('filename')
        actual_filename = actual_asset.pop('filename')
        assert str(expected_key) == expected_filename
        assert str(actual_key) == actual_filename
        assert expected_asset == actual_asset

    def _assertAssetsEqual(self, expected_course_key, expected_assets, actual_course_key, actual_assets):  # pylint: disable=invalid-name
        """
        Private helper method for assertAssetsEqual
        """
        assert len(expected_assets) == len(actual_assets)

        actual_assets_map = {asset['asset_key']: asset for asset in actual_assets}
        for expected_item in expected_assets:
            actual_item = actual_assets_map[expected_item['asset_key'].map_into_course(actual_course_key)]
            self.assertAssetEqual(expected_course_key, expected_item, actual_course_key, actual_item)

    def assertAssetsEqual(self, expected_store, expected_course_key, actual_store, actual_course_key):
        """
        Assert that the course assets identified by ``expected_course_key`` in ``expected_store`` and
        ``actual_course_key`` in ``actual_store`` are identical, allowing for differences related
        to their being from different course keys.
        """
        expected_content, expected_count = expected_store.get_all_content_for_course(expected_course_key)
        actual_content, actual_count = actual_store.get_all_content_for_course(actual_course_key)

        assert expected_count == actual_count
        self._assertAssetsEqual(expected_course_key, expected_content, actual_course_key, actual_content)
        expected_thumbs = expected_store.get_all_content_thumbnails_for_course(expected_course_key)
        actual_thumbs = actual_store.get_all_content_thumbnails_for_course(actual_course_key)
        self._assertAssetsEqual(expected_course_key, expected_thumbs, actual_course_key, actual_thumbs)

    def assertAssetsMetadataEqual(self, expected_modulestore, expected_course_key, actual_modulestore, actual_course_key):  # lint-amnesty, pylint: disable=line-too-long
        """
        Assert that the modulestore asset metdata for the ``expected_course_key`` and the ``actual_course_key``
        are equivalent.
        """
        expected_course_assets = expected_modulestore.get_all_asset_metadata(
            expected_course_key, None, sort=('displayname', ModuleStoreEnum.SortOrder.descending)
        )
        actual_course_assets = actual_modulestore.get_all_asset_metadata(
            actual_course_key, None, sort=('displayname', ModuleStoreEnum.SortOrder.descending)
        )
        assert len(expected_course_assets) == len(actual_course_assets)
        for idx, __ in enumerate(expected_course_assets):
            for attr in AssetMetadata.ATTRS_ALLOWED_TO_UPDATE:
                if attr in ('edited_on',):
                    # edited_on is updated upon import.
                    continue
                assert getattr(expected_course_assets[idx], attr) == getattr(actual_course_assets[idx], attr)
