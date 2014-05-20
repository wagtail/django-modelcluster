from __future__ import unicode_literals

from django.test import TestCase
from django.db import IntegrityError

from tests.models import Band, BandMember, Album

class ClusterTest(TestCase):
    def test_can_create_cluster(self):
        beatles = Band(name='The Beatles')

        self.assertEqual(0, beatles.members.count())

        beatles.members = [
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ]

        # we should be able to query this relation using (some) queryset methods
        self.assertEqual(2, beatles.members.count())
        self.assertEqual('John Lennon', beatles.members.all()[0].name)
        self.assertEqual('Paul McCartney', beatles.members.filter(name='Paul McCartney')[0].name)
        self.assertEqual('Paul McCartney', beatles.members.get(name='Paul McCartney').name)
        self.assertRaises(BandMember.DoesNotExist, lambda: beatles.members.get(name='Reginald Dwight'))
        self.assertRaises(BandMember.MultipleObjectsReturned, lambda: beatles.members.get())

        self.assertEqual([('Paul McCartney',)], beatles.members.filter(name='Paul McCartney').values_list('name'))
        self.assertEqual(['Paul McCartney'], beatles.members.filter(name='Paul McCartney').values_list('name', flat=True))
        # quick-and-dirty check that we can invoke values_list with empty args list
        beatles.members.filter(name='Paul McCartney').values_list()

        # these should not exist in the database yet
        self.assertFalse(Band.objects.filter(name='The Beatles').exists())
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

        beatles.save()
        # this should create database entries
        self.assertTrue(Band.objects.filter(name='The Beatles').exists())
        self.assertTrue(BandMember.objects.filter(name='John Lennon').exists())

        john_lennon = BandMember.objects.get(name='John Lennon')
        beatles.members = [john_lennon]
        # reassigning should take effect on the in-memory record
        self.assertEqual(1, beatles.members.count())
        # but not the database
        self.assertEqual(2, Band.objects.get(name='The Beatles').members.count())

        beatles.save()
        # now updated in the database
        self.assertEqual(1, Band.objects.get(name='The Beatles').members.count())
        self.assertEqual(1, BandMember.objects.filter(name='John Lennon').count())
        # removed member should be deleted from the db entirely
        self.assertEqual(0, BandMember.objects.filter(name='Paul McCartney').count())

        # queries on beatles.members should now revert to SQL
        self.assertTrue(beatles.members.extra(where=["tests_bandmember.name='John Lennon'"]).exists())

    def test_related_manager_assignment_ops(self):
        beatles = Band(name='The Beatles')
        john = BandMember(name='John Lennon')
        paul = BandMember(name='Paul McCartney')

        beatles.members.add(john)
        self.assertEqual(1, beatles.members.count())

        beatles.members.add(paul)
        self.assertEqual(2, beatles.members.count())
        # ensure that duplicates are filtered
        beatles.members.add(paul)
        self.assertEqual(2, beatles.members.count())

        beatles.members.remove(john)
        self.assertEqual(1, beatles.members.count())
        self.assertEqual(paul, beatles.members.all()[0])

        george = beatles.members.create(name='George Harrison')
        self.assertEqual(2, beatles.members.count())
        self.assertEqual('George Harrison', george.name)

    def test_can_pass_child_relations_as_constructor_kwargs(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        self.assertEqual(2, beatles.members.count())
        self.assertEqual(beatles, beatles.members.all()[0].band)

    def test_can_only_commit_on_saved_parent(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        self.assertRaises(IntegrityError, lambda: beatles.members.commit())

        beatles.save()
        beatles.members.commit()

    def test_queryset_filtering(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(id=1, name='John Lennon'),
            BandMember(id=2, name='Paul McCartney'),
        ])
        self.assertEqual('Paul McCartney', beatles.members.get(id=2).name)
        self.assertEqual('Paul McCartney', beatles.members.get(id='2').name)
        self.assertEqual(1, beatles.members.filter(name='Paul McCartney').count())

        # also need to be able to filter on foreign fields that return a model instance
        # rather than a simple python value
        self.assertEqual(2, beatles.members.filter(band=beatles).count())
        # and ensure that the comparison is not treating all unsaved instances as identical
        rutles = Band(name='The Rutles')
        self.assertEqual(0, beatles.members.filter(band=rutles).count())

        # and the comparison must be on the model instance's ID where available,
        # not by reference
        beatles.save()
        beatles.members.add(BandMember(id=3, name='George Harrison'))  # modify the relation so that we're not to a plain database-backed queryset

        also_beatles = Band.objects.get(id=beatles.id)
        self.assertEqual(3, beatles.members.filter(band=also_beatles).count())

    def test_prefetch_related(self):
        band1 = Band.objects.create(name='The Beatles', members=[
            BandMember(id=1, name='John Lennon'),
            BandMember(id=2, name='Paul McCartney'),
        ])
        with self.assertNumQueries(2):
            lists = [list(band.members.all()) for band in Band.objects.prefetch_related('members')]
        normal_lists = [list(band.members.all()) for band in Band.objects.all()]
        self.assertEqual(lists, normal_lists)
