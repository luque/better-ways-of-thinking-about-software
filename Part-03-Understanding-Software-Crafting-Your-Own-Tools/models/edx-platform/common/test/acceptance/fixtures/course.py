"""
Fixture to create a course and course components (XBlocks).
"""


import datetime
import json
import mimetypes
from collections import namedtuple
from textwrap import dedent

from opaque_keys.edx.keys import CourseKey
from path import Path

from common.test.acceptance.fixtures import STUDIO_BASE_URL
from common.test.acceptance.fixtures.base import FixtureError, XBlockContainerFixture
from common.djangoapps.util.course import course_location_from_key


class XBlockFixtureDesc:
    """
    Description of an XBlock, used to configure a course fixture.
    """

    def __init__(self, category, display_name, data=None,
                 metadata=None, grader_type=None, publish='make_public', **kwargs):
        """
        Configure the XBlock to be created by the fixture.
        These arguments have the same meaning as in the Studio REST API:
            * `category`
            * `display_name`
            * `data`
            * `metadata`
            * `grader_type`
            * `publish`
        """
        self.category = category
        self.display_name = display_name
        self.data = data
        self.metadata = metadata
        self.grader_type = grader_type
        self.publish = publish
        self.children = []
        self.locator = None
        self.fields = kwargs

    def add_children(self, *args):
        """
        Add child XBlocks to this XBlock.
        Each item in `args` is an `XBlockFixtureDesc` object.

        Returns the `xblock_desc` instance to allow chaining.
        """
        self.children.extend(args)
        return self

    def serialize(self):
        """
        Return a JSON representation of the XBlock, suitable
        for sending as POST data to /xblock

        XBlocks are always set to public visibility.
        """
        returned_data = {
            'display_name': self.display_name,
            'data': self.data,
            'metadata': self.metadata,
            'graderType': self.grader_type,
            'publish': self.publish,
            'fields': self.fields,
        }
        return json.dumps(returned_data)

    def __str__(self):
        """
        Return a string representation of the description.
        Useful for error messages.
        """
        return dedent("""
            <XBlockFixtureDescriptor:
                category={0},
                data={1},
                metadata={2},
                grader_type={3},
                publish={4},
                children={5},
                locator={6},
            >
        """).strip().format(
            self.category, self.data, self.metadata,
            self.grader_type, self.publish, self.children, self.locator
        )


# Description of course updates to add to the course
# `date` is a str (e.g. "January 29, 2014)
# `content` is also a str (e.g. "Test course")
CourseUpdateDesc = namedtuple("CourseUpdateDesc", ['date', 'content'])


class CourseFixture(XBlockContainerFixture):
    """
    Fixture for ensuring that a course exists.

    WARNING: This fixture is NOT idempotent.  To avoid conflicts
    between tests, you should use unique course identifiers for each fixture.
    """

    def __init__(self, org, number, run, display_name, start_date=None, end_date=None, settings=None):
        """
        Configure the course fixture to create a course with

        `org`, `number`, `run`, and `display_name` (all unicode).

        `start_date` and `end_date` are datetime objects indicating the course start and end date.
        The default is for the course to have started in the distant past, which is generally what
        we want for testing so students can enroll.

        `settings` can be any additional course settings needs to be enabled. for example
        to enable entrance exam settings would be a dict like this {"entrance_exam_enabled": "true"}
        These have the same meaning as in the Studio restful API /course end-point.
        """
        super().__init__()
        self._course_dict = {
            'org': org,
            'number': number,
            'run': run,
            'display_name': display_name
        }

        # Set a default start date to the past, but use Studio's
        # default for the end date (meaning we don't set it here)
        if start_date is None:
            start_date = datetime.datetime(1970, 1, 1)

        self._course_details = {
            'start_date': start_date.isoformat(),
        }

        if end_date is not None:
            self._course_details['end_date'] = end_date.isoformat()

        if settings is not None:
            self._course_details.update(settings)

        self._updates = []
        self._handouts = []
        self._assets = []
        self._textbooks = []
        self._advanced_settings = {}
        self._course_key = None

    def __str__(self):
        """
        String representation of the course fixture, useful for debugging.
        """
        return "<CourseFixture: org='{org}', number='{number}', run='{run}'>".format(**self._course_dict)

    def add_course_details(self, course_details):
        """
        Add course details to dict of course details to be updated when configure_course or install is called.

        Arguments:
            Dictionary containing key value pairs for course updates,
            e.g. {'start_date': datetime.now() }
        """
        if 'start_date' in course_details:
            course_details['start_date'] = course_details['start_date'].isoformat()
        if 'end_date' in course_details:
            course_details['end_date'] = course_details['end_date'].isoformat()

        self._course_details.update(course_details)

    def add_update(self, update):
        """
        Add an update to the course.  `update` should be a `CourseUpdateDesc`.
        """
        self._updates.append(update)

    def add_handout(self, asset_name):
        """
        Add the handout named `asset_name` to the course info page.
        Note that this does not actually *create* the static asset; it only links to it.
        """
        self._handouts.append(asset_name)

    def add_asset(self, asset_name):
        """
        Add the asset to the list of assets to be uploaded when the install method is called.
        """
        self._assets.extend(asset_name)

    def add_textbook(self, book_title, chapters):
        """
        Add textbook to the list of textbooks to be added when the install method is called.
        """
        self._textbooks.append({"chapters": chapters, "tab_title": book_title})

    def add_advanced_settings(self, settings):
        """
        Adds advanced settings to be set on the course when the install method is called.
        """
        self._advanced_settings.update(settings)

    def install(self):
        """
        Create the course and XBlocks within the course.
        This is NOT an idempotent method; if the course already exists, this will
        raise a `FixtureError`.  You should use unique course identifiers to avoid
        conflicts between tests.
        """
        self._create_course()
        self._install_course_updates()
        self._install_course_handouts()
        self._install_course_textbooks()
        self._configure_course()
        self._upload_assets()
        self._add_advanced_settings()
        self._create_xblock_children(self._course_location, self.children)

        return self

    def configure_course(self):
        """
        Configure Course Settings, take new course settings from self._course_details dict object
        """
        self._configure_course()

    @property
    def studio_course_outline_as_json(self):
        """
        Retrieves Studio course outline in JSON format.
        """
        url = STUDIO_BASE_URL + '/course/' + self._course_key + "?format=json"
        response = self.session.get(url, headers=self.headers)

        if not response.ok:
            raise FixtureError(
                "Could not retrieve course outline json.  Status was {}".format(
                    response.status_code))

        try:
            course_outline_json = response.json()
        except ValueError:
            raise FixtureError(  # lint-amnesty, pylint: disable=raise-missing-from
                f"Could not decode course outline as JSON: '{response}'"
            )
        return course_outline_json

    @property
    def _course_location(self):
        """
        Return the locator string for the course.
        """
        course_key = CourseKey.from_string(self._course_key)
        return str(course_location_from_key(course_key))

    @property
    def _assets_url(self):
        """
        Return the url string for the assets
        """
        return "/assets/" + self._course_key + "/"

    @property
    def _handouts_loc(self):
        """
        Return the locator string for the course handouts
        """
        course_key = CourseKey.from_string(self._course_key)
        return str(course_key.make_usage_key('course_info', 'handouts'))

    def _create_course(self):
        """
        Create the course described in the fixture.
        """
        # If the course already exists, this will respond
        # with a 200 and an error message, which we ignore.
        response = self.session.post(
            STUDIO_BASE_URL + '/course/',
            data=self._encode_post_dict(self._course_dict),
            headers=self.headers
        )

        try:
            err = response.json().get('ErrMsg')

        except ValueError:
            raise FixtureError(  # lint-amnesty, pylint: disable=raise-missing-from
                "Could not parse response from course request as JSON: '{}'".format(
                    response.content))

        # This will occur if the course identifier is not unique
        if err is not None:
            raise FixtureError(f"Could not create course {self}.  Error message: '{err}'")

        if response.ok:
            self._course_key = response.json()['course_key']
        else:
            raise FixtureError(
                "Could not create course {}.  Status was {}\nResponse content was: {}".format(
                    self._course_dict, response.status_code, response.content))

    def _configure_course(self):
        """
        Configure course settings (e.g. start and end date)
        """
        url = STUDIO_BASE_URL + '/settings/details/' + self._course_key

        # First, get the current values
        response = self.session.get(url, headers=self.headers)

        if not response.ok:
            raise FixtureError(
                "Could not retrieve course details.  Status was {}".format(
                    response.status_code))

        try:
            details = response.json()
        except ValueError:
            raise FixtureError(  # lint-amnesty, pylint: disable=raise-missing-from
                f"Could not decode course details as JSON: '{details}'"
            )

        # Update the old details with our overrides
        details.update(self._course_details)

        # POST the updated details to Studio
        response = self.session.post(
            url, data=self._encode_post_dict(details),
            headers=self.headers,
        )

        if not response.ok:
            raise FixtureError(
                "Could not update course details to '{}' with {}: Status was {}.".format(
                    self._course_details, url, response.status_code))

    def _install_course_handouts(self):
        """
        Add handouts to the course info page.
        """
        url = STUDIO_BASE_URL + '/xblock/' + self._handouts_loc

        # Construct HTML with each of the handout links
        handouts_li = [
            f'<li><a href="/static/{handout}">Example Handout</a></li>'
            for handout in self._handouts
        ]
        handouts_html = '<ol class="treeview-handoutsnav">{}</ol>'.format("".join(handouts_li))

        # Update the course's handouts HTML
        payload = json.dumps({
            'children': None,
            'data': handouts_html,
            'id': self._handouts_loc,
            'metadata': dict(),
        })

        response = self.session.post(url, data=payload, headers=self.headers)

        if not response.ok:
            raise FixtureError(
                f"Could not update course handouts with {url}.  Status was {response.status_code}")

    def _install_course_updates(self):
        """
        Add updates to the course, if any are configured.
        """
        url = STUDIO_BASE_URL + '/course_info_update/' + self._course_key + '/'

        for update in self._updates:

            # Add the update to the course
            date, content = update
            payload = json.dumps({'date': date, 'content': content})
            response = self.session.post(url, headers=self.headers, data=payload)

            if not response.ok:
                raise FixtureError(
                    "Could not add update to course: {} with {}.  Status was {}".format(
                        update, url, response.status_code))

    def _upload_assets(self):
        """
        Upload assets
        :raise FixtureError:
        """
        url = STUDIO_BASE_URL + self._assets_url

        test_dir = Path(__file__).abspath().dirname().dirname().dirname()

        for asset_name in self._assets:
            asset_file_path = test_dir + '/data/uploads/' + asset_name

            asset_file = open(asset_file_path, mode='rb')  # lint-amnesty, pylint: disable=consider-using-with
            files = {'file': (asset_name, asset_file, mimetypes.guess_type(asset_file_path)[0])}

            headers = {
                'Accept': 'application/json',
                'X-CSRFToken': self.session_cookies.get('csrftoken', '')
            }

            upload_response = self.session.post(url, files=files, headers=headers)

            if not upload_response.ok:
                raise FixtureError('Could not upload {asset_name} with {url}. Status code: {code}'.format(
                    asset_name=asset_name, url=url, code=upload_response.status_code))

    def _install_course_textbooks(self):
        """
        Add textbooks to the course, if any are configured.
        """
        url = STUDIO_BASE_URL + '/textbooks/' + self._course_key

        for book in self._textbooks:
            payload = json.dumps(book)
            response = self.session.post(url, headers=self.headers, data=payload)

            if not response.ok:
                raise FixtureError(
                    "Could not add book to course: {} with {}.  Status was {}".format(
                        book, url, response.status_code))

    def _add_advanced_settings(self):
        """
        Add advanced settings.
        """
        url = STUDIO_BASE_URL + "/settings/advanced/" + self._course_key

        # POST advanced settings to Studio
        response = self.session.post(
            url, data=self._encode_post_dict(self._advanced_settings),
            headers=self.headers,
        )

        if not response.ok:
            raise FixtureError(
                "Could not update advanced details to '{}' with {}: Status was {}.".format(
                    self._advanced_settings, url, response.status_code))

    def _create_xblock_children(self, parent_loc, xblock_descriptions):
        """
        Recursively create XBlock children.
        """
        super()._create_xblock_children(parent_loc, xblock_descriptions)
        self._publish_xblock(parent_loc)
