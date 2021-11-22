"""
Discussion API serializers
"""
from typing import Dict
from urllib.parse import urlencode, urlunparse

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import serializers

from common.djangoapps.student.models import get_user_by_username_or_email
from lms.djangoapps.discussion.django_comment_client.utils import (
    available_division_schemes,
    course_discussion_division_enabled,
    get_group_id_for_user,
    get_group_name,
    get_group_names_by_id,
    is_comment_too_deep,
)
from lms.djangoapps.discussion.rest_api.permissions import (
    NON_UPDATABLE_COMMENT_FIELDS,
    NON_UPDATABLE_THREAD_FIELDS,
    get_editable_fields,
)
from lms.djangoapps.discussion.rest_api.render import render_body
from lms.djangoapps.discussion.views import get_divided_discussions
from openedx.core.djangoapps.django_comment_common.comment_client.comment import Comment
from openedx.core.djangoapps.django_comment_common.comment_client.thread import Thread
from openedx.core.djangoapps.django_comment_common.comment_client.user import User as CommentClientUser
from openedx.core.djangoapps.django_comment_common.comment_client.utils import CommentClientRequestError
from openedx.core.djangoapps.django_comment_common.models import (
    CourseDiscussionSettings,
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_MODERATOR,
    Role,
)

User = get_user_model()


def get_context(course, request, thread=None):
    """
    Returns a context appropriate for use with ThreadSerializer or
    (if thread is provided) CommentSerializer.
    """
    # TODO: cache staff_user_ids and ta_user_ids if we need to improve perf
    staff_user_ids = {
        user.id
        for role in Role.objects.filter(
            name__in=[FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR],
            course_id=course.id
        )
        for user in role.users.all()
    }
    ta_user_ids = {
        user.id
        for role in Role.objects.filter(name=FORUM_ROLE_COMMUNITY_TA, course_id=course.id)
        for user in role.users.all()
    }
    requester = request.user
    cc_requester = CommentClientUser.from_django_user(requester).retrieve()
    cc_requester["course_id"] = course.id
    course_discussion_settings = CourseDiscussionSettings.get(course.id)
    return {
        "course": course,
        "request": request,
        "thread": thread,
        "discussion_division_enabled": course_discussion_division_enabled(course_discussion_settings),
        "group_ids_to_names": get_group_names_by_id(course_discussion_settings),
        "is_requester_privileged": requester.id in staff_user_ids or requester.id in ta_user_ids,
        "staff_user_ids": staff_user_ids,
        "ta_user_ids": ta_user_ids,
        "cc_requester": cc_requester,
    }


def validate_not_blank(value):
    """
    Validate that a value is not an empty string or whitespace.

    Raises: ValidationError
    """
    if not value.strip():
        raise ValidationError("This field may not be blank.")


def _validate_privileged_access(context: Dict) -> bool:
    """
    Return the field specified by ``field_name`` if requesting user is privileged.

    Checks that the course exists in the context, and that the user has privileged
    access.

    Args:
        context (Dict): The serializer context.

    Returns:
        bool: Course exists and the user has privileged access.
    """
    course = context.get('course', None)
    is_requester_privileged = context.get('is_requester_privileged')
    return course and is_requester_privileged


class _ContentSerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    """
    A base class for thread and comment serializers.
    """
    id = serializers.CharField(read_only=True)  # pylint: disable=invalid-name
    author = serializers.SerializerMethodField()
    author_label = serializers.SerializerMethodField()
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)
    raw_body = serializers.CharField(source="body", validators=[validate_not_blank])
    rendered_body = serializers.SerializerMethodField()
    abuse_flagged = serializers.SerializerMethodField()
    voted = serializers.SerializerMethodField()
    vote_count = serializers.SerializerMethodField()
    editable_fields = serializers.SerializerMethodField()

    non_updatable_fields = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.non_updatable_fields:
            setattr(self, f"validate_{field}", self._validate_non_updatable)

    def _validate_non_updatable(self, value):
        """Ensure that a field is not edited in an update operation."""
        if self.instance:
            raise ValidationError("This field is not allowed in an update.")
        return value

    def _is_user_privileged(self, user_id):
        """
        Returns a boolean indicating whether the given user_id identifies a
        privileged user.
        """
        return user_id in self.context["staff_user_ids"] or user_id in self.context["ta_user_ids"]

    def _is_anonymous(self, obj):
        """
        Returns a boolean indicating whether the content should be anonymous to
        the requester.
        """
        return (
            obj["anonymous"] or
            obj["anonymous_to_peers"] and not self.context["is_requester_privileged"]
        )

    def get_author(self, obj):
        """
        Returns the author's username, or None if the content is anonymous.
        """
        return None if self._is_anonymous(obj) else obj["username"]

    def _get_user_label(self, user_id):
        """
        Returns the role label (i.e. "Staff" or "Community TA") for the user
        with the given id.
        """
        return (
            "Staff" if user_id in self.context["staff_user_ids"] else
            "Community TA" if user_id in self.context["ta_user_ids"] else
            None
        )

    def get_author_label(self, obj):
        """
        Returns the role label for the content author.
        """
        if self._is_anonymous(obj) or obj["user_id"] is None:
            return None
        else:
            user_id = int(obj["user_id"])
            return self._get_user_label(user_id)

    def get_rendered_body(self, obj):
        """
        Returns the rendered body content.
        """
        return render_body(obj["body"])

    def get_abuse_flagged(self, obj):
        """
        Returns a boolean indicating whether the requester has flagged the
        content as abusive.
        """
        return self.context["cc_requester"]["id"] in obj.get("abuse_flaggers", [])

    def get_voted(self, obj):
        """
        Returns a boolean indicating whether the requester has voted for the
        content.
        """
        return obj["id"] in self.context["cc_requester"]["upvoted_ids"]

    def get_vote_count(self, obj):
        """
        Returns the number of votes for the content.
        """
        return obj.get("votes", {}).get("up_count", 0)

    def get_editable_fields(self, obj):
        """
        Return the list of the fields the requester can edit
        """
        return sorted(get_editable_fields(obj, self.context))


class ThreadSerializer(_ContentSerializer):
    """
    A serializer for thread data.

    N.B. This should not be used with a comment_client Thread object that has
    not had retrieve() called, because of the interaction between DRF's attempts
    at introspection and Thread's __getattr__.
    """
    course_id = serializers.CharField()
    topic_id = serializers.CharField(source="commentable_id", validators=[validate_not_blank])
    group_id = serializers.IntegerField(required=False, allow_null=True)
    group_name = serializers.SerializerMethodField()
    type = serializers.ChoiceField(
        source="thread_type",
        choices=[(val, val) for val in ["discussion", "question"]]
    )
    abuse_flagged_count = serializers.SerializerMethodField(required=False)
    title = serializers.CharField(validators=[validate_not_blank])
    pinned = serializers.SerializerMethodField(read_only=True)
    closed = serializers.BooleanField(read_only=True)
    following = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField(read_only=True)
    unread_comment_count = serializers.SerializerMethodField(read_only=True)
    comment_list_url = serializers.SerializerMethodField()
    endorsed_comment_list_url = serializers.SerializerMethodField()
    non_endorsed_comment_list_url = serializers.SerializerMethodField()
    read = serializers.BooleanField(required=False)
    has_endorsed = serializers.BooleanField(source="endorsed", read_only=True)
    response_count = serializers.IntegerField(source="resp_total", read_only=True, required=False)

    non_updatable_fields = NON_UPDATABLE_THREAD_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Compensate for the fact that some threads in the comments service do
        # not have the pinned field set
        if self.instance and self.instance.get("pinned") is None:
            self.instance["pinned"] = False

    def get_abuse_flagged_count(self, obj):
        """
        Returns the number of users that flagged content as abusive only if user has staff permissions
        """
        if _validate_privileged_access(self.context):
            return obj.get("abuse_flagged_count")

    def get_pinned(self, obj):
        """
        Compensate for the fact that some threads in the comments service do
        not have the pinned field set.
        """
        return bool(obj["pinned"])

    def get_group_name(self, obj):
        """
        Returns the name of the group identified by the thread's group_id.
        """
        return self.context["group_ids_to_names"].get(obj["group_id"])

    def get_following(self, obj):
        """
        Returns a boolean indicating whether the requester is following the
        thread.
        """
        return obj["id"] in self.context["cc_requester"]["subscribed_thread_ids"]

    def get_comment_list_url(self, obj, endorsed=None):
        """
        Returns the URL to retrieve the thread's comments, optionally including
        the endorsed query parameter.
        """
        if (
                (obj["thread_type"] == "question" and endorsed is None) or
                (obj["thread_type"] == "discussion" and endorsed is not None)
        ):
            return None
        path = reverse("comment-list")
        query_dict = {"thread_id": obj["id"]}
        if endorsed is not None:
            query_dict["endorsed"] = endorsed
        return self.context["request"].build_absolute_uri(
            urlunparse(("", "", path, "", urlencode(query_dict), ""))
        )

    def get_endorsed_comment_list_url(self, obj):
        """
        Returns the URL to retrieve the thread's endorsed comments.
        """
        return self.get_comment_list_url(obj, endorsed=True)

    def get_non_endorsed_comment_list_url(self, obj):
        """
        Returns the URL to retrieve the thread's non-endorsed comments.
        """
        return self.get_comment_list_url(obj, endorsed=False)

    def get_comment_count(self, obj):
        """
        Increments comment count to include post and returns total count of
        contributions (i.e. post + responses + comments) for the thread
        """
        return obj["comments_count"] + 1

    def get_unread_comment_count(self, obj):
        """
        Returns the number of unread comments. If the thread has never been read,
        this additionally includes 1 for the post itself, in addition to its responses and
        comments.
        """
        if not obj["read"] and obj["comments_count"] == obj["unread_comments_count"]:
            return obj["unread_comments_count"] + 1
        return obj["unread_comments_count"]

    def create(self, validated_data):
        thread = Thread(user_id=self.context["cc_requester"]["id"], **validated_data)
        thread.save()
        return thread

    def update(self, instance, validated_data):
        for key, val in validated_data.items():
            instance[key] = val
        instance.save()
        return instance


class CommentSerializer(_ContentSerializer):
    """
    A serializer for comment data.

    N.B. This should not be used with a comment_client Comment object that has
    not had retrieve() called, because of the interaction between DRF's attempts
    at introspection and Comment's __getattr__.
    """
    thread_id = serializers.CharField()
    parent_id = serializers.CharField(required=False, allow_null=True)
    endorsed = serializers.BooleanField(required=False)
    endorsed_by = serializers.SerializerMethodField()
    endorsed_by_label = serializers.SerializerMethodField()
    endorsed_at = serializers.SerializerMethodField()
    child_count = serializers.IntegerField(read_only=True)
    children = serializers.SerializerMethodField(required=False)
    abuse_flagged_any_user = serializers.SerializerMethodField(required=False)

    non_updatable_fields = NON_UPDATABLE_COMMENT_FIELDS

    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        super().__init__(*args, **kwargs)

        if remove_fields:
            # for multiple fields in a list
            for field_name in remove_fields:
                self.fields.pop(field_name)

    def get_endorsed_by(self, obj):
        """
        Returns the username of the endorsing user, if the information is
        available and would not identify the author of an anonymous thread.
        """
        endorsement = obj.get("endorsement")
        if endorsement:
            endorser_id = int(endorsement["user_id"])
            # Avoid revealing the identity of an anonymous non-staff question
            # author who has endorsed a comment in the thread
            if not (
                    self._is_anonymous(self.context["thread"]) and
                    not self._is_user_privileged(endorser_id)
            ):
                return User.objects.get(id=endorser_id).username
        return None

    def get_endorsed_by_label(self, obj):
        """
        Returns the role label (i.e. "Staff" or "Community TA") for the
        endorsing user
        """
        endorsement = obj.get("endorsement")
        if endorsement:
            return self._get_user_label(int(endorsement["user_id"]))
        else:
            return None

    def get_endorsed_at(self, obj):
        """
        Returns the timestamp for the endorsement, if available.
        """
        endorsement = obj.get("endorsement")
        return endorsement["time"] if endorsement else None

    def get_children(self, obj):
        return [
            CommentSerializer(child, context=self.context).data
            for child in obj.get("children", [])
        ]

    def to_representation(self, data):
        # pylint: disable=arguments-differ
        data = super().to_representation(data)

        # Django Rest Framework v3 no longer includes None values
        # in the representation.  To maintain the previous behavior,
        # we do this manually instead.
        if 'parent_id' not in data:
            data["parent_id"] = None

        return data

    def get_abuse_flagged_any_user(self, obj):
        """
        Returns a boolean indicating whether any user has flagged the
        content as abusive.
        """
        if _validate_privileged_access(self.context):
            return len(obj.get("abuse_flaggers", [])) > 0

    def validate(self, attrs):
        """
        Ensure that parent_id identifies a comment that is actually in the
        thread identified by thread_id and does not violate the configured
        maximum depth.
        """
        parent = None
        parent_id = attrs.get("parent_id")
        if parent_id:
            try:
                parent = Comment(id=parent_id).retrieve()
            except CommentClientRequestError:
                pass
            if not (parent and parent["thread_id"] == attrs["thread_id"]):
                raise ValidationError(
                    "parent_id does not identify a comment in the thread identified by thread_id."
                )
        if is_comment_too_deep(parent):
            raise ValidationError("Comment level is too deep.")
        return attrs

    def create(self, validated_data):
        comment = Comment(
            course_id=self.context["thread"]["course_id"],
            user_id=self.context["cc_requester"]["id"],
            **validated_data
        )
        comment.save()
        return comment

    def update(self, instance, validated_data):
        for key, val in validated_data.items():
            instance[key] = val
            # TODO: The comments service doesn't populate the endorsement
            # field on comment creation, so we only provide
            # endorsement_user_id on update
            if key == "endorsed":
                instance["endorsement_user_id"] = self.context["cc_requester"]["id"]

        instance.save()
        return instance


class DiscussionTopicSerializer(serializers.Serializer):
    """
    Serializer for DiscussionTopic
    """
    id = serializers.CharField(read_only=True)  # pylint: disable=invalid-name
    name = serializers.CharField(read_only=True)
    thread_list_url = serializers.CharField(read_only=True)
    children = serializers.SerializerMethodField()

    def get_children(self, obj):
        """
        Returns a list of children of DiscussionTopicSerializer type
        """
        if not obj.children:
            return []
        return [DiscussionTopicSerializer(child).data for child in obj.children]

    def create(self, validated_data):
        """
        Overriden create abstract method
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass

    def update(self, instance, validated_data):
        """
        Overriden update abstract method
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass


class DiscussionSettingsSerializer(serializers.Serializer):
    """
    Serializer for course discussion settings.
    """
    divided_discussions = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
    )
    divided_course_wide_discussions = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
    )
    divided_inline_discussions = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
    )
    always_divide_inline_discussions = serializers.BooleanField()
    division_scheme = serializers.CharField()

    def to_internal_value(self, data: dict) -> dict:
        """
        Transform the *incoming* primitive data into a native value.
        """
        payload = super().to_internal_value(data) or {}
        course = self.context['course']
        instance = self.context['settings']
        if any(item in data for item in ('divided_course_wide_discussions', 'divided_inline_discussions')):
            divided_course_wide_discussions, divided_inline_discussions = get_divided_discussions(
                course, instance
            )
            divided_course_wide_discussions = data.get(
                'divided_course_wide_discussions',
                divided_course_wide_discussions
            )
            divided_inline_discussions = data.get('divided_inline_discussions', divided_inline_discussions)
            try:
                payload['divided_discussions'] = divided_course_wide_discussions + divided_inline_discussions
            except TypeError as error:
                raise ValidationError(str(error)) from error
        for item in ('always_divide_inline_discussions', 'division_scheme'):
            if item in data:
                payload[item] = data[item]
        return payload

    def to_representation(self, instance: CourseDiscussionSettings) -> dict:
        """
        Return a serialized representation of the course discussion settings.
        """
        payload = super().to_representation(instance)
        course = self.context['course']
        instance = self.context['settings']
        course_key = course.id
        divided_course_wide_discussions, divided_inline_discussions = get_divided_discussions(
            course, instance
        )
        payload = {
            'id': instance.id,
            'divided_inline_discussions': divided_inline_discussions,
            'divided_course_wide_discussions': divided_course_wide_discussions,
            'always_divide_inline_discussions': instance.always_divide_inline_discussions,
            'division_scheme': instance.division_scheme,
            'available_division_schemes': available_division_schemes(course_key)
        }
        return payload

    def create(self, validated_data):
        """
        This method intentionally left empty
        """

    def update(self, instance: CourseDiscussionSettings, validated_data: dict) -> CourseDiscussionSettings:
        """
        Update and save an existing instance
        """
        if not any(field in validated_data for field in self.fields):
            raise ValidationError('Bad request')
        try:
            instance.update(validated_data)
        except ValueError as e:
            raise ValidationError(str(e)) from e
        return instance


class DiscussionRolesSerializer(serializers.Serializer):
    """
    Serializer for course discussion roles.
    """

    ACTION_CHOICES = (
        ('allow', 'allow'),
        ('revoke', 'revoke')
    )
    action = serializers.ChoiceField(ACTION_CHOICES)
    user_id = serializers.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate_user_id(self, user_id):  # lint-amnesty, pylint: disable=missing-function-docstring
        try:
            self.user = get_user_by_username_or_email(user_id)
            return user_id
        except User.DoesNotExist:
            raise ValidationError(f"'{user_id}' is not a valid student identifier")  # lint-amnesty, pylint: disable=raise-missing-from

    def validate(self, attrs):
        """Validate the data at an object level."""

        # Store the user object to avoid fetching it again.
        if hasattr(self, 'user'):
            attrs['user'] = self.user
        return attrs

    def create(self, validated_data):
        """
        Overriden create abstract method
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass

    def update(self, instance, validated_data):
        """
        Overriden update abstract method
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass


class DiscussionRolesMemberSerializer(serializers.Serializer):
    """
    Serializer for course discussion roles member data.
    """
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    group_name = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_discussion_settings = self.context['course_discussion_settings']

    def get_group_name(self, instance):
        """Return the group name of the user."""
        group_id = get_group_id_for_user(instance, self.course_discussion_settings)
        group_name = get_group_name(group_id, self.course_discussion_settings)
        return group_name

    def create(self, validated_data):
        """
        Overriden create abstract method
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass

    def update(self, instance, validated_data):
        """
        Overriden update abstract method
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass


class DiscussionRolesListSerializer(serializers.Serializer):
    """
    Serializer for course discussion roles member list.
    """
    course_id = serializers.CharField()
    results = serializers.SerializerMethodField()
    division_scheme = serializers.SerializerMethodField()

    def get_results(self, obj):
        """Return the nested serializer data representing a list of member users."""
        context = {
            'course_id': obj['course_id'],
            'course_discussion_settings': self.context['course_discussion_settings']
        }
        serializer = DiscussionRolesMemberSerializer(obj['users'], context=context, many=True)
        return serializer.data

    def get_division_scheme(self, obj):  # pylint: disable=unused-argument
        """Return the division scheme for the course."""
        return self.context['course_discussion_settings'].division_scheme

    def create(self, validated_data):
        """
        Overriden create abstract method
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass

    def update(self, instance, validated_data):
        """
        Overriden update abstract method
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass
