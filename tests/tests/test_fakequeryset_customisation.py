from __future__ import unicode_literals

from django.db import models
from django.test import TestCase

from modelcluster.queryset import (
    FAKEQUERYSET_COMPATIBLE_METHOD_ATTR,
    FakeQuerySet,
    QuerySetMethodOrAttributeUnavailableError,
    fakequeryset_compatible,
    get_fake_queryset_for_model,
)
from tests.models import Band, BandMember


class FakeQuerySetCustomisationTest(TestCase):
    def test_decorated_queryset_helpers_available_on_fake_queryset(self):
        beatles = Band(
            name="The Beatles",
            members=[
                BandMember(name="John Lennon"),
                BandMember(name="Paul McCartney"),
                BandMember(name="Ringo Starr"),
            ],
        )

        self.assertEqual(
            ["Paul McCartney"], [member.name for member in beatles.members.named_paul()]
        )
        self.assertEqual(
            ["Paul McCartney"],
            [member.name for member in beatles.members.names_starting_with("Paul")],
        )

    def test_undecorated_queryset_helpers_not_available_on_fake_queryset(self):
        beatles = Band(
            name="The Beatles",
            members=[BandMember(name="John Lennon"), BandMember(name="Paul McCartney")],
        )

        with self.assertRaisesMessage(
            QuerySetMethodOrAttributeUnavailableError,
            "only has access to explicitly registered custom queryset methods",
        ):
            beatles.members.db_only_helper()

    def test_fakequeryset_factory_from_instances(self):
        queryset = FakeQuerySet.from_instances(
            [BandMember(name="John Lennon"), BandMember(name="Paul McCartney")]
        )
        self.assertIsNot(type(queryset), FakeQuerySet)
        self.assertEqual(
            ["Paul McCartney"], [member.name for member in queryset.named_paul()]
        )

        empty_queryset = FakeQuerySet.from_instances([], model=BandMember)
        self.assertEqual([], list(empty_queryset.named_paul()))

        self.assertRaises(ValueError, lambda: FakeQuerySet.from_instances([]))
        self.assertRaises(
            TypeError,
            lambda: FakeQuerySet.from_instances(
                [BandMember(name="Paul McCartney")], model=Band
            ),
        )

    def test_get_fakequeryset_for_model_uses_decorated_helpers(self):
        queryset = get_fake_queryset_for_model(
            BandMember,
            [BandMember(name="John Lennon"), BandMember(name="Paul McCartney")],
        )

        self.assertEqual(type(queryset).__name__, "FakeBandMemberQuerySet")
        self.assertEqual(
            ["Paul McCartney"], [member.name for member in queryset.named_paul()]
        )

    def test_fakequeryset_compatible_alias_can_replace_db_method_name(self):
        beatles = Band(
            name="The Beatles",
            members=[BandMember(name="John Lennon"), BandMember(name="Paul McCartney")],
        )

        self.assertEqual(
            ["John Lennon", "Paul McCartney"],
            [member.name for member in beatles.members.with_name_uppercase()],
        )

    def test_fakequeryset_compatible_alias_conflict_is_ignored(self):
        with self.assertLogs("modelcluster.queryset", level="WARNING") as captured_logs:

            class ConflictingAliasQuerySet(models.QuerySet):
                @fakequeryset_compatible(as_name="filter")
                def fake_filter_alias(self):
                    return self

        self.assertEqual(
            len(captured_logs.output),
            1,
        )
        self.assertIn(
            "fakequeryset_compatible registered method name 'filter' conflicts with FakeQuerySet.filter. Overrides are not supported, so the custom method is ignored",
            captured_logs.output[0],
        )
        self.assertFalse(
            getattr(
                ConflictingAliasQuerySet.fake_filter_alias,
                FAKEQUERYSET_COMPATIBLE_METHOD_ATTR,
                False,
            )
        )

    def test_fakequeryset_compatible_default_name_conflict_is_ignored(self):
        with self.assertLogs("modelcluster.queryset", level="WARNING") as captured_logs:

            class ConflictingMethodNameQuerySet(models.QuerySet):
                @fakequeryset_compatible
                def filter(self, *args, **kwargs):
                    return self

        self.assertEqual(
            len(captured_logs.output),
            1,
        )
        self.assertIn(
            "fakequeryset_compatible registered method name 'filter' conflicts with FakeQuerySet.filter. Overrides are not supported, so the custom method is ignored",
            captured_logs.output[0],
        )
        self.assertFalse(
            getattr(
                ConflictingMethodNameQuerySet.filter,
                FAKEQUERYSET_COMPATIBLE_METHOD_ATTR,
                False,
            )
        )

    def test_fakequeryset_compatible_methods_are_inherited_from_queryset_bases(self):
        class ThirdPartyPageQuerySet(models.QuerySet):
            @fakequeryset_compatible
            def third_party_helper(self):
                return "third-party"

        class EventPageQuerySet(ThirdPartyPageQuerySet):
            pass

        class EventPage(models.Model):
            objects = EventPageQuerySet.as_manager()

            class Meta:
                abstract = True

        fake_queryset = get_fake_queryset_for_model(EventPage, [])
        self.assertEqual(fake_queryset.third_party_helper(), "third-party")

    def test_fakequeryset_compatible_subclass_override_wins(self):
        class ThirdPartyPageQuerySet(models.QuerySet):
            @fakequeryset_compatible
            def helper_source(self):
                return "third-party"

        class EventPageQuerySet(ThirdPartyPageQuerySet):
            @fakequeryset_compatible
            def helper_source(self):
                return "project"

        class EventPage(models.Model):
            objects = EventPageQuerySet.as_manager()

            class Meta:
                abstract = True

        fake_queryset = get_fake_queryset_for_model(EventPage, [])
        self.assertEqual(fake_queryset.helper_source(), "project")

    def test_model_inheritance_without_queryset_inheritance_does_not_copy_helpers(self):
        class ThirdPartyPageQuerySet(models.QuerySet):
            @fakequeryset_compatible
            def third_party_helper(self):
                return "third-party"

        class Page(models.Model):
            objects = ThirdPartyPageQuerySet.as_manager()

            class Meta:
                abstract = True

        class EventPageQuerySet(models.QuerySet):
            @fakequeryset_compatible
            def event_helper(self):
                return "event"

        class EventPage(Page):
            objects = EventPageQuerySet.as_manager()

            class Meta:
                abstract = True

        fake_queryset = get_fake_queryset_for_model(EventPage, [])
        self.assertEqual(fake_queryset.event_helper(), "event")
        with self.assertRaises(QuerySetMethodOrAttributeUnavailableError):
            fake_queryset.third_party_helper()
