from __future__ import unicode_literals

import json
import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from tests.models import Band, BandMember, Album, Place, Restaurant, SeafoodRestaurant, Dish, \
    MenuItem, Chef, Wine, Review, Log, Document, Article, Author, Category


class SerializeTest(TestCase):
    def test_serialize(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])

        expected = {'pk': None, 'albums': [], 'name': 'The Beatles', 'members': [
            {'pk': None, 'name': 'John Lennon', 'band': None, 'favourite_restaurant': None},
            {'pk': None, 'name': 'Paul McCartney', 'band': None, 'favourite_restaurant': None}
        ]}
        self.assertEqual(expected, beatles.serializable_data())

    def test_serialize_m2m(self):
        george_orwell = Author.objects.create(name='George Orwell')
        charles_dickens = Author.objects.create(name='Charles Dickens')

        article = Article(
            title='Down and Out in Paris and London',
            authors=[george_orwell, charles_dickens],
        )

        article_serialised = article.serializable_data()
        self.assertEqual(article_serialised['title'], 'Down and Out in Paris and London')
        self.assertIn(george_orwell.pk, article_serialised['authors'])
        self.assertEqual(article_serialised['categories'], [])

    def test_serialize_json_with_dates(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ], albums=[
            Album(name='Rubber Soul', release_date=datetime.date(1965, 12, 3))
        ])

        beatles_json = beatles.to_json()
        self.assertTrue("John Lennon" in beatles_json)
        self.assertTrue("1965-12-03" in beatles_json)
        unpacked_beatles = Band.from_json(beatles_json)
        self.assertEqual(datetime.date(1965, 12, 3), unpacked_beatles.albums.all()[0].release_date)

    def test_deserialize(self):
        beatles = Band.from_serializable_data({
            'pk': 9,
            'albums': [],
            'name': 'The Beatles',
            'members': [
                {'pk': None, 'name': 'John Lennon', 'band': None},
                {'pk': None, 'name': 'Paul McCartney', 'band': None},
            ]
        })
        self.assertEqual(9, beatles.id)
        self.assertEqual('The Beatles', beatles.name)
        self.assertEqual(2, beatles.members.count())
        self.assertEqual(BandMember, beatles.members.all()[0].__class__)

    def test_deserialize_m2m(self):
        authors = {}
        categories = {}
        for i in range(1, 6):
            authors[i] = Author.objects.create(name="Author %d" % i)
            categories[i] = Category.objects.create(name="Category %d" % i)

        article = Article.from_serializable_data({
            'pk': 1,
            'title': 'Article Title 1',
            'authors': [authors[1].pk, authors[2].pk],
            'categories': [categories[2].pk, categories[3].pk, categories[4].pk]
        })
        self.assertEqual(article.id, 1)
        self.assertEqual(article.title, 'Article Title 1')
        self.assertEqual(article.authors.count(), 2)
        self.assertEqual(
            [author.name for author in article.authors.order_by('name')],
            ['Author 1', 'Author 2']
        )
        self.assertEqual(article.categories.count(), 3)

    def test_deserialize_json(self):
        beatles = Band.from_json('{"pk": 9, "albums": [], "name": "The Beatles", "members": [{"pk": null, "name": "John Lennon", "band": null}, {"pk": null, "name": "Paul McCartney", "band": null}]}')
        self.assertEqual(9, beatles.id)
        self.assertEqual('The Beatles', beatles.name)
        self.assertEqual(2, beatles.members.count())
        self.assertEqual(BandMember, beatles.members.all()[0].__class__)

    def test_serialize_with_multi_table_inheritance(self):
        fat_duck = Restaurant(name='The Fat Duck', serves_hot_dogs=False, reviews=[
            Review(author='Michael Winner', body='Rubbish.')
        ])
        data = json.loads(fat_duck.to_json())
        self.assertEqual(data['name'], 'The Fat Duck')
        self.assertEqual(data['serves_hot_dogs'], False)
        self.assertEqual(data['reviews'][0]['author'], 'Michael Winner')

    def test_deserialize_with_multi_table_inheritance(self):
        fat_duck = Restaurant.from_json('{"pk": 42, "name": "The Fat Duck", "serves_hot_dogs": false, "reviews": [{"pk": null, "author": "Michael Winner", "body": "Rubbish."}]}')
        self.assertEqual(fat_duck.id, 42)
        self.assertEqual(fat_duck.name, "The Fat Duck")
        self.assertEqual(fat_duck.serves_hot_dogs, False)
        self.assertEqual(fat_duck.reviews.all()[0].author, "Michael Winner")

    def test_deserialize_with_second_level_multi_table_inheritance(self):
        oyster_club = SeafoodRestaurant.from_json('{"pk": 43, "name": "The Oyster Club"}')
        self.assertEqual(oyster_club.id, 43)
        self.assertEqual(oyster_club.restaurant_ptr_id, 43)
        self.assertEqual(oyster_club.place_ptr_id, 43)
        self.assertEqual(oyster_club.restaurant_ptr.__class__, Restaurant)
        self.assertEqual(oyster_club.place_ptr.__class__, Place)
        self.assertEqual(oyster_club.name, "The Oyster Club")

    def test_dangling_foreign_keys(self):
        heston_blumenthal = Chef.objects.create(name="Heston Blumenthal")
        snail_ice_cream = Dish.objects.create(name="Snail ice cream")
        chateauneuf = Wine.objects.create(name="Chateauneuf-du-Pape 1979")
        fat_duck = Restaurant(name="The Fat Duck", proprietor=heston_blumenthal, serves_hot_dogs=False, menu_items=[
            MenuItem(dish=snail_ice_cream, price='20.00', recommended_wine=chateauneuf)
        ])
        fat_duck_json = fat_duck.to_json()

        fat_duck = Restaurant.from_json(fat_duck_json)
        self.assertEqual("Heston Blumenthal", fat_duck.proprietor.name)
        self.assertEqual("Chateauneuf-du-Pape 1979", fat_duck.menu_items.all()[0].recommended_wine.name)

        heston_blumenthal.delete()
        fat_duck = Restaurant.from_json(fat_duck_json)
        # the deserialised record should recognise that the heston_blumenthal record is now missing
        self.assertEqual(None, fat_duck.proprietor)
        self.assertEqual("Chateauneuf-du-Pape 1979", fat_duck.menu_items.all()[0].recommended_wine.name)

        chateauneuf.delete()  # oh dear, looks like we just drank the last bottle
        fat_duck = Restaurant.from_json(fat_duck_json)
        # the deserialised record should now have a null recommended_wine field
        self.assertEqual(None, fat_duck.menu_items.all()[0].recommended_wine)

        snail_ice_cream.delete()  # NOM NOM NOM
        fat_duck = Restaurant.from_json(fat_duck_json)
        # the menu item should now be dropped entirely (because the foreign key to Dish has on_delete=CASCADE)
        self.assertEqual(0, fat_duck.menu_items.count())

    def test_deserialize_with_sort_order(self):
        beatles = Band.from_json('{"pk": null, "albums": [{"pk": null, "name": "With The Beatles", "sort_order": 2}, {"pk": null, "name": "Please Please Me", "sort_order": 1}], "name": "The Beatles", "members": []}')
        self.assertEqual(2, beatles.albums.count())

        # Make sure the albums were ordered correctly
        self.assertEqual("Please Please Me", beatles.albums.all()[0].name)
        self.assertEqual("With The Beatles", beatles.albums.all()[1].name)

    def test_deserialize_with_reversed_sort_order(self):
        Album._meta.ordering = ['-sort_order']
        beatles = Band.from_json('{"pk": null, "albums": [{"pk": null, "name": "Please Please Me", "sort_order": 1}, {"pk": null, "name": "With The Beatles", "sort_order": 2}], "name": "The Beatles", "members": []}')
        Album._meta.ordering = ['sort_order']
        self.assertEqual(2, beatles.albums.count())

        # Make sure the albums were ordered correctly
        self.assertEqual("With The Beatles", beatles.albums.all()[0].name)
        self.assertEqual("Please Please Me", beatles.albums.all()[1].name)

    def test_deserialize_with_multiple_sort_order(self):
        Album._meta.ordering = ['sort_order', 'name']
        beatles = Band.from_json('{"pk": null, "albums": [{"pk": 1, "name": "With The Beatles", "sort_order": 1}, {"pk": 2, "name": "Please Please Me", "sort_order": 1}, {"pk": 3, "name": "Please Please Me", "sort_order": 2}], "name": "The Beatles", "members": []}')
        Album._meta.ordering = ['sort_order']
        self.assertEqual(3, beatles.albums.count())

        # Make sure the albums were ordered correctly
        self.assertEqual(2, beatles.albums.all()[0].pk)
        self.assertEqual(1, beatles.albums.all()[1].pk)
        self.assertEqual(3, beatles.albums.all()[2].pk)

    WAGTAIL_05_RELEASE_DATETIME = datetime.datetime(2014, 8, 1, 11, 1, 42)

    def test_serialise_with_naive_datetime(self):
        """
        This tests that naive datetimes are saved as UTC
        """
        # Time is in America/Chicago time
        log = Log(time=self.WAGTAIL_05_RELEASE_DATETIME, data="Wagtail 0.5 released")
        log_json = json.loads(log.to_json())

        # Now check that the time is stored correctly with the timezone information at the end
        self.assertEqual(log_json['time'], '2014-08-01T16:01:42Z')

    def test_serialise_with_aware_datetime(self):
        """
        This tests that aware datetimes are converted to as UTC
        """
        # make an aware datetime, consisting of WAGTAIL_05_RELEASE_DATETIME
        # in a timezone 1hr west of UTC
        one_hour_west = timezone.get_fixed_timezone(-60)

        local_time = timezone.make_aware(self.WAGTAIL_05_RELEASE_DATETIME, one_hour_west)
        log = Log(time=local_time, data="Wagtail 0.5 released")
        log_json = json.loads(log.to_json())

        # Now check that the time is stored correctly with the timezone information at the end
        self.assertEqual(log_json['time'], '2014-08-01T12:01:42Z')

    def test_deserialise_with_utc_datetime(self):
        """
        This tests that a datetimes saved as UTC are converted back correctly
        """
        # Time is in UTC
        log = Log.from_json('{"data": "Wagtail 0.5 released", "time": "2014-08-01T16:01:42Z", "pk": null}')

        # Naive and aware timezones cannot be compared so make the release date timezone-aware before comparison
        expected_time = timezone.make_aware(self.WAGTAIL_05_RELEASE_DATETIME, timezone.get_default_timezone())

        # Check that the datetime is correct and was converted back into the correct timezone
        self.assertEqual(log.time, expected_time)
        self.assertEqual(log.time.tzinfo, expected_time.tzinfo)

    def test_deserialise_with_local_datetime(self):
        """
        This tests that a datetime without timezone information is interpreted as a local time
        """
        log = Log.from_json('{"data": "Wagtail 0.5 released", "time": "2014-08-01T11:01:42", "pk": null}')

        expected_time = timezone.make_aware(self.WAGTAIL_05_RELEASE_DATETIME, timezone.get_default_timezone())
        self.assertEqual(log.time, expected_time)
        self.assertEqual(log.time.tzinfo, expected_time.tzinfo)

    def test_serialise_with_null_datetime(self):
        log = Log(time=None, data="Someone scanned a QR code")
        log_json = json.loads(log.to_json())
        self.assertEqual(log_json['time'], None)

    def test_deserialise_with_null_datetime(self):
        log = Log.from_json('{"data": "Someone scanned a QR code", "time": null, "pk": null}')
        self.assertEqual(log.time, None)

    def test_serialise_saves_file_fields(self):
        doc = Document(title='Hello')
        doc.file = SimpleUploadedFile('hello.txt', b'Hello world')

        doc_json = doc.to_json()
        new_doc = Document.from_json(doc_json)

        self.assertEqual(new_doc.file.read(), b'Hello world')

    def test_ignored_relations(self):
        george_orwell = Author.objects.create(name='George Orwell')
        charles_dickens = Author.objects.create(name='Charles Dickens')

        rel_article = Article(
            title='Round and round wherever',
            authors=[george_orwell],
        )
        article = Article(
            title='Down and Out in Paris and London',
            authors=[george_orwell, charles_dickens],
            related_articles=[rel_article],
            view_count=123
        )

        article_serialised = article.serializable_data()
        # check that related_articles and view_count are not serialized (marked with serialize=False)
        self.assertNotIn('related_articles', article_serialised)
        self.assertNotIn('view_count', article_serialised)

        rel_article.save()
        article.save()

        article_json = article.to_json()
        restored_article = Article.from_json(article_json)
        restored_article.save()
        restored_article = Article.objects.get(pk=restored_article.pk)
        # check that related_articles and view_count hasn't been touched
        self.assertIn(rel_article, restored_article.related_articles.all())
