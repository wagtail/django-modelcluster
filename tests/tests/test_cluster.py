from __future__ import unicode_literals

import datetime
import itertools

from django.test import TestCase
from django.db import IntegrityError
from django.db.models import Prefetch

from modelcluster.models import get_all_child_relations
from modelcluster.queryset import FakeQuerySet
from modelcluster.utils import ManyToManyTraversalError

from tests.models import Band, BandMember, Chef, Feature, Place, Restaurant, SeafoodRestaurant, \
    Review, Album, Article, Author, Category, Person, Room, House, Log, Dish, MenuItem, Wine


class ClusterTest(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.gordon_ramsay = Chef.objects.create(name="Gordon Ramsay")
        cls.strawberry_fields = Restaurant.objects.create(name="Strawberry Fields", proprietor=cls.gordon_ramsay)

        cls.marco_pierre_white = Chef.objects.create(name="Marco Pierre White")
        cls.the_yellow_submarine = Restaurant.objects.create(name="The Yellow Submarine", proprietor=cls.marco_pierre_white)

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
        self.assertEqual('Paul McCartney', beatles.members.filter(name__exact='Paul McCartney')[0].name)
        self.assertEqual('Paul McCartney', beatles.members.filter(name__iexact='paul mccartNEY')[0].name)

        self.assertEqual(0, beatles.members.filter(name__lt='B').count())
        self.assertEqual(1, beatles.members.filter(name__lt='M').count())
        self.assertEqual('John Lennon', beatles.members.filter(name__lt='M')[0].name)
        self.assertEqual(1, beatles.members.filter(name__lt='Paul McCartney').count())
        self.assertEqual('John Lennon', beatles.members.filter(name__lt='Paul McCartney')[0].name)
        self.assertEqual(2, beatles.members.filter(name__lt='Z').count())

        self.assertEqual(0, beatles.members.filter(name__lte='B').count())
        self.assertEqual(1, beatles.members.filter(name__lte='M').count())
        self.assertEqual('John Lennon', beatles.members.filter(name__lte='M')[0].name)
        self.assertEqual(2, beatles.members.filter(name__lte='Paul McCartney').count())
        self.assertEqual(2, beatles.members.filter(name__lte='Z').count())

        self.assertEqual(2, beatles.members.filter(name__gt='B').count())
        self.assertEqual(1, beatles.members.filter(name__gt='M').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__gt='M')[0].name)
        self.assertEqual(0, beatles.members.filter(name__gt='Paul McCartney').count())

        self.assertEqual(2, beatles.members.filter(name__gte='B').count())
        self.assertEqual(1, beatles.members.filter(name__gte='M').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__gte='M')[0].name)
        self.assertEqual(1, beatles.members.filter(name__gte='Paul McCartney').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__gte='Paul McCartney')[0].name)
        self.assertEqual(0, beatles.members.filter(name__gte='Z').count())

        self.assertEqual(1, beatles.members.filter(name__contains='Cart').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__contains='Cart')[0].name)
        self.assertEqual(1, beatles.members.filter(name__icontains='carT').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__icontains='carT')[0].name)

        self.assertEqual(1, beatles.members.filter(name__in=['Paul McCartney', 'Linda McCartney']).count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__in=['Paul McCartney', 'Linda McCartney'])[0].name)

        self.assertEqual(1, beatles.members.filter(name__startswith='Paul').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__startswith='Paul')[0].name)
        self.assertEqual(1, beatles.members.filter(name__istartswith='pauL').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__istartswith='pauL')[0].name)
        self.assertEqual(1, beatles.members.filter(name__endswith='ney').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__endswith='ney')[0].name)
        self.assertEqual(1, beatles.members.filter(name__iendswith='Ney').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__iendswith='Ney')[0].name)

        self.assertEqual('Paul McCartney', beatles.members.get(name='Paul McCartney').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__exact='Paul McCartney').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__iexact='paul mccartNEY').name)
        self.assertEqual('John Lennon', beatles.members.get(name__lt='Paul McCartney').name)
        self.assertEqual('John Lennon', beatles.members.get(name__lte='M').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__gt='M').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__gte='Paul McCartney').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__contains='Cart').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__icontains='carT').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__in=['Paul McCartney', 'Linda McCartney']).name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__startswith='Paul').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__istartswith='pauL').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__endswith='ney').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__iendswith='Ney').name)

        self.assertEqual('John Lennon', beatles.members.get(name__regex=r'n{2}').name)
        self.assertEqual('John Lennon', beatles.members.get(name__iregex=r'N{2}').name)

        self.assertRaises(BandMember.DoesNotExist, lambda: beatles.members.get(name='Reginald Dwight'))
        self.assertRaises(BandMember.MultipleObjectsReturned, lambda: beatles.members.get())

        self.assertTrue(beatles.members.filter(name='Paul McCartney').exists())
        self.assertFalse(beatles.members.filter(name='Reginald Dwight').exists())

        self.assertEqual('John Lennon', beatles.members.first().name)
        self.assertEqual('Paul McCartney', beatles.members.last().name)

        self.assertTrue('John Lennon', beatles.members.order_by('name').first())
        self.assertTrue('Paul McCartney', beatles.members.order_by('-name').first())

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

    def test_values_list(self):
        beatles = Band(
            name="The Beatles",
            members=[
                BandMember(name="John Lennon", favourite_restaurant=self.strawberry_fields),
                BandMember(name="Paul McCartney", favourite_restaurant=self.the_yellow_submarine),
                BandMember(name="George Harrison"),
                BandMember(name="Ringo Starr"),
            ],
        )

        # Not specifying 'fields' should return a tuple of all field values
        self.assertEqual(
            [
                # ID, band_id, name, favourite_restaurant_id
                (None, None, 'Paul McCartney', self.the_yellow_submarine.id)
            ],
            list(beatles.members.filter(name='Paul McCartney').values_list())
        )

        NAME_ONLY_TUPLE = ('Paul McCartney',)

        # Specifying 'fields' should return a tuple of just those field values
        self.assertEqual([NAME_ONLY_TUPLE], list(beatles.members.filter(name='Paul McCartney').values_list('name')))

        # 'fields' can span relationships using '__'
        members = beatles.members.all().values_list('name', 'favourite_restaurant__proprietor__name')
        self.assertEqual(
            list(members),
            [
                ("John Lennon", "Gordon Ramsay"),
                ("Paul McCartney", "Marco Pierre White"),
                ("George Harrison", None),
                ("Ringo Starr", None),
            ]
        )

        # Ordering on the related fields will work too, and items with `None`` values will appear first
        self.assertEqual(
            list(members.order_by('favourite_restaurant__proprietor__name')),
            [
                ("George Harrison", None),
                ("Ringo Starr", None),
                ("John Lennon", "Gordon Ramsay"),
                ("Paul McCartney", "Marco Pierre White"),

            ]
        )

        # get() should return a tuple if used after values_list()
        self.assertEqual(NAME_ONLY_TUPLE, beatles.members.filter(name='Paul McCartney').values_list('name').get())

        # first() should return a tuple if used after values_list()
        self.assertEqual(NAME_ONLY_TUPLE, beatles.members.filter(name='Paul McCartney').values_list('name').first())

        # last() should return a tuple if used after values_list()
        self.assertEqual(NAME_ONLY_TUPLE, beatles.members.filter(name='Paul McCartney').values_list('name').last())

        # And the 'flat' argument should work as it does in Django
        self.assertEqual(['Paul McCartney'], list(beatles.members.filter(name='Paul McCartney').values_list('name', flat=True)))

        # Filtering or ordering after using values_list() should not raise an error
        beatles.members.values_list("name").filter(name__contains="n").order_by("name")

    def test_values(self):
        beatles = Band(
            name="The Beatles",
            members=[
                BandMember(name="John Lennon", favourite_restaurant=self.strawberry_fields),
                BandMember(name="Paul McCartney", favourite_restaurant=self.the_yellow_submarine),
                BandMember(name="George Harrison"),
                BandMember(name="Ringo Starr"),
            ],
        )

        # Not specifying 'fields' should return dictionaries with all field values
        self.assertEqual(
            [
                {"id": None, "band": None, "name": "Paul McCartney", "favourite_restaurant": self.the_yellow_submarine.id}
            ],
            list(beatles.members.filter(name='Paul McCartney').values())
        )

        NAME_ONLY_DICT = {"name": "Paul McCartney"}

        # Specifying 'fields' should return a dictionary of just those field values
        self.assertEqual([NAME_ONLY_DICT], list(beatles.members.filter(name='Paul McCartney').values('name')))

        # 'fields' can span relationships using '__'
        members = beatles.members.all().values('name', 'favourite_restaurant__proprietor__name')
        self.assertEqual(
            list(members),
            [
                {"name": "John Lennon", "favourite_restaurant__proprietor__name": "Gordon Ramsay"},
                {"name": "Paul McCartney", "favourite_restaurant__proprietor__name": "Marco Pierre White"},
                {"name": "George Harrison", "favourite_restaurant__proprietor__name": None},
                {"name": "Ringo Starr", "favourite_restaurant__proprietor__name": None},
            ]
        )

        # Ordering on the related fields will work too, and items with `None`` values will appear first
        self.assertEqual(
            list(members.order_by('favourite_restaurant__proprietor__name')),
            [
                {"name": "George Harrison", "favourite_restaurant__proprietor__name": None},
                {"name": "Ringo Starr", "favourite_restaurant__proprietor__name": None},
                {"name": "John Lennon", "favourite_restaurant__proprietor__name": "Gordon Ramsay"},
                {"name": "Paul McCartney", "favourite_restaurant__proprietor__name": "Marco Pierre White"},
            ]
        )

        # get() should return a dict if used after values()
        self.assertEqual(NAME_ONLY_DICT, beatles.members.filter(name='Paul McCartney').values('name').get())

        # first() should return a dict if used after values_list()
        self.assertEqual(NAME_ONLY_DICT, beatles.members.filter(name='Paul McCartney').values('name').first())

        # last() should return a dict if used after values_list()
        self.assertEqual(NAME_ONLY_DICT, beatles.members.filter(name='Paul McCartney').values('name').last())

        # Filtering or ordering after using values() should not raise an error
        beatles.members.values("name").filter(name__contains="n").order_by("name")

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

        beatles.members.set([john])
        self.assertEqual(1, beatles.members.count())
        self.assertEqual(john, beatles.members.all()[0])

    def test_can_pass_child_relations_as_constructor_kwargs(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        self.assertEqual(2, beatles.members.count())
        self.assertEqual(beatles, beatles.members.all()[0].band)

    def test_can_access_child_relations_of_superclass(self):
        fat_duck = Restaurant(name='The Fat Duck', serves_hot_dogs=False, reviews=[
            Review(author='Michael Winner', body='Rubbish.')
        ])
        self.assertEqual(1, fat_duck.reviews.count())
        self.assertEqual(fat_duck.reviews.first().author, 'Michael Winner')
        self.assertEqual(fat_duck, fat_duck.reviews.all()[0].place)

        fat_duck.save()
        # ensure relations have been saved to the database
        fat_duck = Restaurant.objects.get(id=fat_duck.id)
        self.assertEqual(1, fat_duck.reviews.count())
        self.assertEqual(fat_duck.reviews.first().author, 'Michael Winner')

    def test_can_only_commit_on_saved_parent(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        self.assertRaises(IntegrityError, lambda: beatles.members.commit())

        beatles.save()
        beatles.members.commit()

    def test_integrity_error_with_none_pk(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        beatles.save()
        beatles.pk = None
        self.assertRaises(IntegrityError, lambda: beatles.members.commit())
        # this should work fine, as Django will end up cloning this entity
        beatles.save()
        self.assertEqual(Band.objects.get(pk=beatles.pk).name, 'The Beatles')

    def test_model_with_zero_pk(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        beatles.save()
        beatles.pk = 0
        beatles.members.commit()
        beatles.save()
        self.assertEqual(Band.objects.get(pk=0).name, 'The Beatles')

    def test_save_with_update_fields(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ], albums=[
            Album(name='Please Please Me', sort_order=1),
            Album(name='With The Beatles', sort_order=2),
            Album(name='Abbey Road', sort_order=3),
        ])

        beatles.save()

        # modify both relations, but only commit the change to members
        beatles.members.clear()
        beatles.albums.clear()
        beatles.name = 'The Rutles'
        beatles.save(update_fields=['name', 'members'])

        updated_beatles = Band.objects.get(pk=beatles.pk)
        self.assertEqual(updated_beatles.name, 'The Rutles')
        self.assertEqual(updated_beatles.members.count(), 0)
        self.assertEqual(updated_beatles.albums.count(), 3)

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

    def test_queryset_filtering_on_models_with_inheritance(self):
        john = BandMember(name='John Lennon', favourite_restaurant=self.strawberry_fields)
        ringo = BandMember(name='Ringo Starr', favourite_restaurant=Restaurant.objects.get(name='The Yellow Submarine'))

        beatles = Band(name='The Beatles', members=[john, ringo])

        # queried instance is less specific
        self.assertEqual(
            list(beatles.members.filter(favourite_restaurant=Place.objects.get(name='Strawberry Fields'))),
            [john]
        )

        # queried instance is more specific
        self.assertEqual(
            list(beatles.members.filter(favourite_restaurant=self.the_yellow_submarine)),
            [ringo]
        )

    def test_queryset_exclude_filtering(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(id=1, name='John Lennon'),
            BandMember(id=2, name='Paul McCartney'),
        ])

        self.assertEqual(1, beatles.members.exclude(name='Paul McCartney').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name='Paul McCartney').first().name)

        self.assertEqual(1, beatles.members.exclude(name__exact='Paul McCartney').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__exact='Paul McCartney').first().name)
        self.assertEqual(1, beatles.members.exclude(name__iexact='paul mccartNEY').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__iexact='paul mccartNEY').first().name)

        self.assertEqual(1, beatles.members.exclude(name__lt='M').count())
        self.assertEqual('Paul McCartney', beatles.members.exclude(name__lt='M').first().name)
        self.assertEqual(1, beatles.members.exclude(name__lt='Paul McCartney').count())
        self.assertEqual('Paul McCartney', beatles.members.exclude(name__lt='Paul McCartney').first().name)

        self.assertEqual(1, beatles.members.exclude(name__lte='John Lennon').count())
        self.assertEqual('Paul McCartney', beatles.members.exclude(name__lte='John Lennon').first().name)

        self.assertEqual(1, beatles.members.exclude(name__gt='M').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__gt='M').first().name)
        self.assertEqual(1, beatles.members.exclude(name__gte='Paul McCartney').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__gte='Paul McCartney').first().name)

        self.assertEqual(1, beatles.members.exclude(name__contains='Cart').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__contains='Cart').first().name)
        self.assertEqual(1, beatles.members.exclude(name__icontains='carT').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__icontains='carT').first().name)

        self.assertEqual(1, beatles.members.exclude(name__in=['Paul McCartney', 'Linda McCartney']).count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__in=['Paul McCartney', 'Linda McCartney'])[0].name)

        self.assertEqual(1, beatles.members.exclude(name__startswith='Paul').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__startswith='Paul').first().name)
        self.assertEqual(1, beatles.members.exclude(name__istartswith='pauL').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__istartswith='pauL').first().name)
        self.assertEqual(1, beatles.members.exclude(name__endswith='ney').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__endswith='ney').first().name)
        self.assertEqual(1, beatles.members.exclude(name__iendswith='Ney').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__iendswith='Ney').first().name)

    def test_queryset_filter_with_nulls(self):
        tmbg = Band(name="They Might Be Giants", albums=[
            Album(name="Flood", release_date=datetime.date(1990, 1, 1)),
            Album(name="John Henry", release_date=datetime.date(1994, 7, 21)),
            Album(name="Factory Showroom", release_date=datetime.date(1996, 3, 30)),
            Album(name="", release_date=None),
            Album(name=None, release_date=None),
        ])

        self.assertEqual(tmbg.albums.get(name="Flood").name, "Flood")
        self.assertEqual(tmbg.albums.get(name="").name, "")
        self.assertEqual(tmbg.albums.get(name=None).name, None)

        self.assertEqual(tmbg.albums.get(name__exact="Flood").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__exact="").name, "")
        self.assertEqual(tmbg.albums.get(name__exact=None).name, None)

        self.assertEqual(tmbg.albums.get(name__iexact="flood").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__iexact="").name, "")
        self.assertEqual(tmbg.albums.get(name__iexact=None).name, None)

        self.assertEqual(tmbg.albums.get(name__contains="loo").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__icontains="LOO").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__startswith="Flo").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__istartswith="flO").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__endswith="ood").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__iendswith="Ood").name, "Flood")

        self.assertEqual(tmbg.albums.get(name__lt="A").name, "")
        self.assertEqual(tmbg.albums.get(name__lte="A").name, "")
        self.assertEqual(tmbg.albums.get(name__gt="J").name, "John Henry")
        self.assertEqual(tmbg.albums.get(name__gte="J").name, "John Henry")

        self.assertEqual(tmbg.albums.get(name__in=["Flood", "Mink Car"]).name, "Flood")
        self.assertEqual(tmbg.albums.get(name__in=["", "Mink Car"]).name, "")
        self.assertEqual(tmbg.albums.get(name__in=[None, "Mink Car"]).name, None)

        self.assertEqual(tmbg.albums.filter(name__isnull=True).count(), 1)
        self.assertEqual(tmbg.albums.filter(name__isnull=False).count(), 4)

        self.assertEqual(tmbg.albums.get(name__regex=r'l..d').name, "Flood")
        self.assertEqual(tmbg.albums.get(name__iregex=r'f..o').name, "Flood")

    def test_date_filters(self):
        tmbg = Band(name="They Might Be Giants", albums=[
            Album(name="Flood", release_date=datetime.date(1990, 1, 1)),
            Album(name="John Henry", release_date=datetime.date(1994, 7, 21)),
            Album(name="Factory Showroom", release_date=datetime.date(1996, 3, 30)),
            Album(name="The Complete Dial-A-Song", release_date=None),
        ])

        logs = FakeQuerySet(Log, [
            Log(time=datetime.datetime(1979, 7, 1, 1, 1, 1), data="nobody died"),
            Log(time=datetime.datetime(1980, 2, 2, 2, 2, 2), data="one person died"),
            Log(time=None, data="nothing happened")
        ])

        self.assertEqual(
            tmbg.albums.get(release_date__range=(datetime.date(1994, 1, 1), datetime.date(1994, 12, 31))).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__range=(datetime.datetime(1980, 1, 1, 1, 1, 1), datetime.datetime(1980, 12, 31, 23, 59, 59))).data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__date=datetime.date(1994, 7, 21)).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__date=datetime.date(1980, 2, 2)).data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__year='1994').name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__year=1980).data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__month=7).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__month='2').data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__day='21').name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__day=2).data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__week=29).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__week='5').data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__week_day=5).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__week_day=7).data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__quarter=3).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__quarter=1).data,
            "one person died"
        )

        self.assertEqual(
            logs.get(time__time=datetime.time(2, 2, 2)).data,
            "one person died"
        )

        self.assertEqual(
            logs.get(time__hour=2).data,
            "one person died"
        )

        self.assertEqual(
            logs.get(time__minute='2').data,
            "one person died"
        )

        self.assertEqual(
            logs.get(time__second=2).data,
            "one person died"
        )

    def test_queryset_filtering_accross_foreignkeys(self):
        band = Band(
            name="The Beatles",
            members=[
                BandMember(name="John Lennon", favourite_restaurant=self.strawberry_fields),
                BandMember(name="Ringo Starr", favourite_restaurant=self.the_yellow_submarine)
            ],
        )

        # Filter over a single relationship
        # ---------------------------------------
        # Using the default/exact lookup type
        self.assertEqual(
            tuple(band.members.filter(favourite_restaurant__name="Strawberry Fields")),
            (band.members.get(name="John Lennon"),)
        )
        self.assertEqual(
            tuple(band.members.filter(favourite_restaurant__name="The Yellow Submarine")),
            (band.members.get(name="Ringo Starr"),)
        )
        # Using an alternative lookup type
        self.assertEqual(
            tuple(band.members.filter(favourite_restaurant__name__icontains="straw")),
            (band.members.get(name="John Lennon"),)
        )
        self.assertEqual(
            tuple(band.members.filter(favourite_restaurant__name__icontains="yello")),
            (band.members.get(name="Ringo Starr"),)
        )

        # Filtering over 2 relationships
        # ---------------------------------------
        # Using a default/exact field lookup
        self.assertEqual(
            tuple(band.members.filter(favourite_restaurant__proprietor__name="Gordon Ramsay")),
            (band.members.get(name="John Lennon"),)
        )
        self.assertEqual(
            tuple(band.members.filter(favourite_restaurant__proprietor__name="Marco Pierre White")),
            (band.members.get(name="Ringo Starr"),)
        )
        # Using an alternative lookup type
        self.assertEqual(
            tuple(band.members.filter(favourite_restaurant__proprietor__name__iexact="gORDON rAMSAY")),
            (band.members.get(name="John Lennon"),)
        )
        self.assertEqual(
            tuple(band.members.filter(favourite_restaurant__proprietor__name__iexact="mARCO pIERRE wHITE")),
            (band.members.get(name="Ringo Starr"),)
        )
        # Using an exact proprietor comparisson
        self.assertEqual(
            tuple(band.members.filter(favourite_restaurant__proprietor=self.gordon_ramsay)),
            (band.members.get(name="John Lennon"),)
        )
        self.assertEqual(
            tuple(band.members.filter(favourite_restaurant__proprietor=self.marco_pierre_white)),
            (band.members.get(name="Ringo Starr"),)
        )

    def test_filtering_via_reverse_foreignkey(self):
        band = Band(
            name="The Beatles",
            members=[
                BandMember(name="John Lennon"),
                BandMember(name="Ringo Starr"),
            ],
        )
        self.assertEqual(
            tuple(band.members.filter(band__name="The Beatles")),
            tuple(band.members.all())
        )
        self.assertEqual(
            tuple(band.members.filter(band__name="The Monkeys")),
            ()
        )

    def test_ordering_accross_foreignkeys(self):
        band = Band(
            name="The Beatles",
            members=[
                BandMember(name="John Lennon", favourite_restaurant=self.strawberry_fields),
                BandMember(name="Ringo Starr", favourite_restaurant=self.the_yellow_submarine),
            ],
        )

        # Ordering accross a single relationship
        # ---------------------------------------
        self.assertEqual(
            tuple(band.members.order_by("favourite_restaurant__name")),
            (
                band.members.get(name="John Lennon"),
                band.members.get(name="Ringo Starr"),
            )
        )
        # How about ordering in reverse?
        self.assertEqual(
            tuple(band.members.order_by("-favourite_restaurant__name")),
            (
                band.members.get(name="Ringo Starr"),
                band.members.get(name="John Lennon"),
            )
        )

        # Ordering accross 2 relationships
        # --------------------------------
        self.assertEqual(
            tuple(band.members.order_by("favourite_restaurant__proprietor__name")),
            (
                band.members.get(name="John Lennon"),
                band.members.get(name="Ringo Starr"),
            )
        )
        # How about ordering in reverse?
        self.assertEqual(
            tuple(band.members.order_by("-favourite_restaurant__proprietor__name")),
            (
                band.members.get(name="Ringo Starr"),
                band.members.get(name="John Lennon"),
            )
        )

    def test_filtering_via_manytomany_raises_exception(self):
        bay_window = Feature.objects.create(name="Bay window", desirability=6)
        underfloor_heating = Feature.objects.create(name="Underfloor heading", desirability=10)
        open_fire = Feature.objects.create(name="Open fire", desirability=3)
        log_burner = Feature.objects.create(name="Log burner", desirability=10)

        modern_living_room = Room.objects.create(name="Modern living room", features=[bay_window, underfloor_heating, log_burner])
        classic_living_room = Room.objects.create(name="Classic living room", features=[bay_window, open_fire])

        modern_house = House.objects.create(name="Modern house", address="1 Yellow Brick Road", main_room=modern_living_room)
        classic_house = House.objects.create(name="Classic house", address="3 Yellow Brick Road", main_room=classic_living_room)

        tenant = Person(
            name="Alex", houses=[modern_house, classic_house]
        )

        with self.assertRaises(ManyToManyTraversalError):
            tenant.houses.filter(main_room__features__name="Bay window")

    def test_prefetch_related(self):
        Band.objects.create(name='The Beatles', members=[
            BandMember(id=1, name='John Lennon'),
            BandMember(id=2, name='Paul McCartney'),
        ])
        with self.assertNumQueries(2):
            lists = [list(band.members.all()) for band in Band.objects.prefetch_related('members')]
        normal_lists = [list(band.members.all()) for band in Band.objects.all()]
        self.assertEqual(lists, normal_lists)

    def test_prefetch_related_with_custom_queryset(self):
        from django.db.models import Prefetch
        Band.objects.create(name='The Beatles', members=[
            BandMember(id=1, name='John Lennon'),
            BandMember(id=2, name='Paul McCartney'),
        ])
        with self.assertNumQueries(2):
            lists = [
                list(band.members.all())
                for band in Band.objects.prefetch_related(
                    Prefetch('members', queryset=BandMember.objects.filter(name__startswith='Paul'))
                )
            ]
        normal_lists = [list(band.members.filter(name__startswith='Paul')) for band in Band.objects.all()]
        self.assertEqual(lists, normal_lists)

    def test_order_by_with_multiple_fields(self):
        beatles = Band(name='The Beatles', albums=[
            Album(name='Please Please Me', sort_order=2),
            Album(name='With The Beatles', sort_order=1),
            Album(name='Abbey Road', sort_order=2),
        ])

        albums = [album.name for album in beatles.albums.order_by('sort_order', 'name')]
        self.assertEqual(['With The Beatles', 'Abbey Road', 'Please Please Me'], albums)

        albums = [album.name for album in beatles.albums.order_by('sort_order', '-name')]
        self.assertEqual(['With The Beatles', 'Please Please Me', 'Abbey Road'], albums)

    def test_meta_ordering(self):
        beatles = Band(name='The Beatles', albums=[
            Album(name='Please Please Me', sort_order=2),
            Album(name='With The Beatles', sort_order=1),
            Album(name='Abbey Road', sort_order=3),
        ])

        # in the absence of an explicit order_by clause, it should use the ordering as defined
        # in Album.Meta, which is 'sort_order'
        albums = [album.name for album in beatles.albums.all()]
        self.assertEqual(['With The Beatles', 'Please Please Me', 'Abbey Road'], albums)

    def test_parental_key_checks_clusterable_model(self):
        from django.core import checks
        from django.db import models
        from modelcluster.fields import ParentalKey

        class Instrument(models.Model):
            # Oops, BandMember is not a Clusterable model
            member = ParentalKey(BandMember, on_delete=models.CASCADE)

            class Meta:
                # Prevent Django from thinking this is in the database
                # This shouldn't affect the test
                abstract = True

        # Check for error
        errors = Instrument.check()
        self.assertEqual(1, len(errors))

        # Check the error itself
        error = errors[0]
        self.assertIsInstance(error, checks.Error)
        self.assertEqual(error.id, 'modelcluster.E001')
        self.assertEqual(error.obj, Instrument.member.field)
        self.assertEqual(error.msg, 'ParentalKey must point to a subclass of ClusterableModel.')
        self.assertEqual(error.hint, 'Change tests.BandMember into a ClusterableModel or use a ForeignKey instead.')

    def test_parental_key_checks_related_name_is_not_plus(self):
        from django.core import checks
        from django.db import models
        from modelcluster.fields import ParentalKey

        class Instrument(models.Model):
            # Oops, related_name='+' is not allowed
            band = ParentalKey(Band, related_name='+', on_delete=models.CASCADE)

            class Meta:
                # Prevent Django from thinking this is in the database
                # This shouldn't affect the test
                abstract = True

        # Check for error
        errors = Instrument.check()
        self.assertEqual(1, len(errors))

        # Check the error itself
        error = errors[0]
        self.assertIsInstance(error, checks.Error)
        self.assertEqual(error.id, 'modelcluster.E002')
        self.assertEqual(error.obj, Instrument.band.field)
        self.assertEqual(error.msg, "related_name='+' is not allowed on ParentalKey fields")
        self.assertEqual(error.hint, "Either change it to a valid name or remove it")

    def test_parental_key_checks_target_is_resolved_as_class(self):
        from django.core import checks
        from django.db import models
        from modelcluster.fields import ParentalKey

        class Instrument(models.Model):
            banana = ParentalKey('Banana', on_delete=models.CASCADE)

            class Meta:
                # Prevent Django from thinking this is in the database
                # This shouldn't affect the test
                abstract = True

        # Check for error
        errors = Instrument.check()
        self.assertEqual(1, len(errors))

        # Check the error itself
        error = errors[0]
        self.assertIsInstance(error, checks.Error)
        self.assertEqual(error.id, 'fields.E300')
        self.assertEqual(error.obj, Instrument.banana.field)
        self.assertEqual(error.msg, "Field defines a relation with model 'Banana', which is either not installed, or is abstract.")


class GetAllChildRelationsTest(TestCase):
    def test_get_all_child_relations(self):
        self.assertEqual(
            set([rel.name for rel in get_all_child_relations(Restaurant)]),
            set(['tagged_items', 'reviews', 'menu_items'])
        )


class ParentalM2MTest(TestCase):
    def setUp(self):
        self.article = Article(title="Test Title")
        self.author_1 = Author.objects.create(name="Author 1")
        self.author_2 = Author.objects.create(name="Author 2")
        self.article.authors = [self.author_1, self.author_2]
        self.category_1 = Category.objects.create(name="Category 1")
        self.category_2 = Category.objects.create(name="Category 2")
        self.article.categories = [self.category_1, self.category_2]

    def test_uninitialised_m2m_relation(self):
        # Reading an m2m relation of a newly created object should return an empty queryset
        new_article = Article(title="Test title")
        self.assertEqual([], list(new_article.authors.all()))
        self.assertEqual(new_article.authors.count(), 0)

        # the manager should have a 'model' property pointing to the target model
        self.assertEqual(Author, new_article.authors.model)

    def test_parentalm2mfield(self):
        # Article should not exist in the database yet
        self.assertFalse(Article.objects.filter(title='Test Title').exists())

        # Test lookup on parental M2M relation
        self.assertEqual(
            ['Author 1', 'Author 2'],
            [author.name for author in self.article.authors.order_by('name')]
        )
        self.assertEqual(self.article.authors.count(), 2)

        # the manager should have a 'model' property pointing to the target model
        self.assertEqual(Author, self.article.authors.model)

        # Test adding to the relation
        author_3 = Author.objects.create(name="Author 3")
        self.article.authors.add(author_3)
        self.assertEqual(
            ['Author 1', 'Author 2', 'Author 3'],
            [author.name for author in self.article.authors.all().order_by('name')]
        )
        self.assertEqual(self.article.authors.count(), 3)

        # Test removing from the relation
        self.article.authors.remove(author_3)
        self.assertEqual(
            ['Author 1', 'Author 2'],
            [author.name for author in self.article.authors.order_by('name')]
        )
        self.assertEqual(self.article.authors.count(), 2)

        # Test clearing the relation
        self.article.authors.clear()
        self.assertEqual(
            [],
            [author.name for author in self.article.authors.order_by('name')]
        )
        self.assertEqual(self.article.authors.count(), 0)

        # Test the 'set' operation
        self.article.authors.set([self.author_2])
        self.assertEqual(self.article.authors.count(), 1)
        self.assertEqual(
            ['Author 2'],
            [author.name for author in self.article.authors.order_by('name')]
        )

        # Test saving to / restoring from DB
        self.article.authors = [self.author_1, self.author_2]
        self.article.save()
        self.article = Article.objects.get(title="Test Title")
        self.assertEqual(
            ['Author 1', 'Author 2'],
            [author.name for author in self.article.authors.order_by('name')]
        )
        self.assertEqual(self.article.authors.count(), 2)

    def test_constructor(self):
        # Test passing values for M2M relations as kwargs to the constructor
        article2 = Article(
            title="Test article 2",
            authors=[self.author_1],
            categories=[self.category_2],
        )
        self.assertEqual(
            ['Author 1'],
            [author.name for author in article2.authors.order_by('name')]
        )
        self.assertEqual(article2.authors.count(), 1)

    def test_ordering(self):
        # our fake querysets should respect the ordering defined on the target model
        bela_bartok = Author.objects.create(name='Bela Bartok')
        graham_greene = Author.objects.create(name='Graham Greene')
        janis_joplin = Author.objects.create(name='Janis Joplin')
        simon_sharma = Author.objects.create(name='Simon Sharma')
        william_wordsworth = Author.objects.create(name='William Wordsworth')

        article3 = Article(title="Test article 3")
        article3.authors = [
            janis_joplin, william_wordsworth, bela_bartok, simon_sharma, graham_greene
        ]
        self.assertEqual(
            list(article3.authors.all()),
            [bela_bartok, graham_greene, janis_joplin, simon_sharma, william_wordsworth]
        )

    def test_save_m2m_with_update_fields(self):
        self.article.save()

        # modify both relations, but only commit the change to authors
        self.article.authors.clear()
        self.article.categories.clear()
        self.article.title = 'Updated title'
        self.article.save(update_fields=['title', 'authors'])

        self.updated_article = Article.objects.get(pk=self.article.pk)
        self.assertEqual(self.updated_article.title, 'Updated title')
        self.assertEqual(self.updated_article.authors.count(), 0)
        self.assertEqual(self.updated_article.categories.count(), 2)

    def test_reverse_m2m_field(self):
        # article is unsaved, so should not be returned by the reverse relation on author
        self.assertEqual(self.author_1.articles_by_author.count(), 0)

        self.article.save()
        # should now be able to look up on the reverse relation
        self.assertEqual(self.author_1.articles_by_author.count(), 1)
        self.assertEqual(self.author_1.articles_by_author.get(), self.article)

        article_2 = Article(title="Test Title 2")
        article_2.authors = [self.author_1]
        article_2.save()
        self.assertEqual(self.author_1.articles_by_author.all().count(), 2)
        self.assertEqual(
            list(self.author_1.articles_by_author.order_by('title').values_list('title', flat=True)),
            ['Test Title', 'Test Title 2']
        )

    def test_value_from_object(self):
        authors_field = Article._meta.get_field('authors')
        self.assertEqual(
            set(authors_field.value_from_object(self.article)),
            set([self.author_1, self.author_2])
        )
        self.article.save()
        self.assertEqual(
            set(authors_field.value_from_object(self.article)),
            set([self.author_1, self.author_2])
        )


class ParentalManyToManyPrefetchTests(TestCase):
    def setUp(self):
        # Create 10 articles with 10 authors each.
        authors = Author.objects.bulk_create(
            Author(id=i, name=str(i)) for i in range(10)
        )
        authors = Author.objects.all()

        for i in range(10):
            article = Article(title=str(i))
            article.authors = authors
            article.save()

    def get_author_names(self, articles):
        return [
            author.name
            for article in articles
            for author in article.authors.all()
        ]

    def test_prefetch_related(self):
        with self.assertNumQueries(11):
            names = self.get_author_names(Article.objects.all())

        with self.assertNumQueries(2):
            prefetched_names = self.get_author_names(
                Article.objects.prefetch_related('authors')
            )

        self.assertEqual(names, prefetched_names)

    def test_prefetch_related_with_custom_queryset(self):
        from django.db.models import Prefetch

        with self.assertNumQueries(2):
            names = self.get_author_names(
                Article.objects.prefetch_related(
                    Prefetch('authors', queryset=Author.objects.filter(name__lt='5'))
                )
            )

        self.assertEqual(len(names), 50)

    def test_prefetch_from_fake_queryset(self):
        article = Article(title='Article with related articles')
        article.related_articles = list(Article.objects.all())

        with self.assertNumQueries(10):
            names = self.get_author_names(article.related_articles.all())

        with self.assertNumQueries(1):
            prefetched_names = self.get_author_names(
                article.related_articles.prefetch_related('authors')
            )

        self.assertEqual(names, prefetched_names)


class PrefetchRelatedTest(TestCase):
    def test_fakequeryset_prefetch_related(self):
        person1 = Person.objects.create(name='Joe')
        person2 = Person.objects.create(name='Mary')

        # Set main_room for each house before creating the next one for
        # databases where supports_nullable_unique_constraints is False.

        house1 = House.objects.create(name='House 1', address='123 Main St', owner=person1)
        room1_1 = Room.objects.create(name='Dining room')
        room1_2 = Room.objects.create(name='Lounge')
        room1_3 = Room.objects.create(name='Kitchen')
        house1.main_room = room1_1
        house1.save()

        house2 = House(name='House 2', address='45 Side St', owner=person1)
        room2_1 = Room.objects.create(name='Eating room')
        room2_2 = Room.objects.create(name='TV Room')
        room2_3 = Room.objects.create(name='Bathroom')
        house2.main_room = room2_1

        person1.houses = itertools.chain(House.objects.all(), [house2])

        houses = person1.houses.all()

        with self.assertNumQueries(1):
            qs = person1.houses.prefetch_related('main_room')

        with self.assertNumQueries(0):
            main_rooms = [ house.main_room for house in person1.houses.all() ]
            self.assertEqual(len(main_rooms), 2)

    def test_prefetch_related_with_lookup(self):
        restaurant1 = Restaurant.objects.create(name='The Jolly Beaver')
        restaurant2 = Restaurant.objects.create(name='The Prancing Rhino')
        dish1 = Dish.objects.create(name='Goodies')
        dish2 = Dish.objects.create(name='Baddies')
        wine1 = Wine.objects.create(name='Chateau1')
        wine2 = Wine.objects.create(name='Chateau2')
        menu_item1 = MenuItem.objects.create(restaurant=restaurant1, dish=dish1, recommended_wine=wine1, price=1)
        menu_item2 = MenuItem.objects.create(restaurant=restaurant2, dish=dish2, recommended_wine=wine2, price=10)

        query = Restaurant.objects.all().prefetch_related(
            Prefetch('menu_items', queryset=MenuItem.objects.only('price', 'recommended_wine').select_related('recommended_wine'))
        )

        res = list(query)
        self.assertEqual(query[0].menu_items.all()[0], menu_item1)
        self.assertEqual(query[1].menu_items.all()[0], menu_item2)
