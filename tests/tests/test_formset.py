from __future__ import unicode_literals

from django.test import TestCase
from modelcluster.forms import transientmodelformset_factory, childformset_factory
from tests.models import NewsPaper, Article, Author, Band, BandMember, Album


class TransientFormsetTest(TestCase):
    BandMembersFormset = transientmodelformset_factory(BandMember, exclude=['band'], extra=3, can_delete=True)

    def test_can_create_formset(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        band_members_formset = self.BandMembersFormset(queryset=beatles.members.all())

        self.assertEqual(5, len(band_members_formset.forms))
        self.assertEqual('John Lennon', band_members_formset.forms[0].instance.name)

    def test_incoming_formset_data(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='George Harrison'),
        ])

        band_members_formset = self.BandMembersFormset({
            'form-TOTAL_FORMS': 3,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-id': '',

            'form-1-name': 'Paul McCartney',
            'form-1-id': '',

            'form-2-name': '',
            'form-2-id': '',
        }, queryset=beatles.members.all())

        self.assertTrue(band_members_formset.is_valid())
        members = band_members_formset.save(commit=False)
        self.assertEqual(2, len(members))
        self.assertEqual('John Lennon', members[0].name)
        # should not exist in the database yet
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

    def test_save_commit_false(self):
        john = BandMember(name='John Lennon')
        paul = BandMember(name='Paul McCartney')
        ringo = BandMember(name='Richard Starkey')
        beatles = Band(name='The Beatles', members=[
            john, paul, ringo
        ])
        beatles.save()

        john_id, paul_id, ringo_id = john.id, paul.id, ringo.id

        self.assertTrue(john_id)
        self.assertTrue(paul_id)

        band_members_formset = self.BandMembersFormset({
            'form-TOTAL_FORMS': 5,
            'form-INITIAL_FORMS': 3,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-DELETE': 'form-0-DELETE',
            'form-0-id': john_id,

            'form-1-name': 'Paul McCartney',
            'form-1-id': paul_id,

            'form-2-name': 'Ringo Starr',  # changing data of an existing record
            'form-2-id': ringo_id,

            'form-3-name': '',
            'form-3-id': '',

            'form-4-name': 'George Harrison',  # Adding a record
            'form-4-id': '',
        }, queryset=beatles.members.all())
        self.assertTrue(band_members_formset.is_valid())

        updated_members = band_members_formset.save(commit=False)
        self.assertEqual(2, len(updated_members))
        self.assertEqual('Ringo Starr', updated_members[0].name)
        self.assertEqual(ringo_id, updated_members[0].id)

        # should not be updated in the db yet
        self.assertEqual('Richard Starkey', BandMember.objects.get(id=ringo_id).name)

        self.assertEqual('George Harrison', updated_members[1].name)
        self.assertFalse(updated_members[1].id)  # no ID yet

    def test_save_commit_true(self):
        john = BandMember(name='John Lennon')
        paul = BandMember(name='Paul McCartney')
        ringo = BandMember(name='Richard Starkey')
        beatles = Band(name='The Beatles', members=[
            john, paul, ringo
        ])
        beatles.save()

        john_id, paul_id, ringo_id = john.id, paul.id, ringo.id

        self.assertTrue(john_id)
        self.assertTrue(paul_id)

        band_members_formset = self.BandMembersFormset({
            'form-TOTAL_FORMS': 4,
            'form-INITIAL_FORMS': 3,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-DELETE': 'form-0-DELETE',
            'form-0-id': john_id,

            'form-1-name': 'Paul McCartney',
            'form-1-id': paul_id,

            'form-2-name': 'Ringo Starr',  # changing data of an existing record
            'form-2-id': ringo_id,

            'form-3-name': '',
            'form-3-id': '',
        }, queryset=beatles.members.all())
        self.assertTrue(band_members_formset.is_valid())

        updated_members = band_members_formset.save()
        self.assertEqual(1, len(updated_members))
        self.assertEqual('Ringo Starr', updated_members[0].name)
        self.assertEqual(ringo_id, updated_members[0].id)

        self.assertFalse(BandMember.objects.filter(id=john_id).exists())
        self.assertEqual('Paul McCartney', BandMember.objects.get(id=paul_id).name)
        self.assertEqual(beatles.id, BandMember.objects.get(id=paul_id).band_id)
        self.assertEqual('Ringo Starr', BandMember.objects.get(id=ringo_id).name)
        self.assertEqual(beatles.id, BandMember.objects.get(id=ringo_id).band_id)


class ChildFormsetTest(TestCase):
    def test_can_create_formset(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        BandMembersFormset = childformset_factory(Band, BandMember, extra=3)
        band_members_formset = BandMembersFormset(instance=beatles)

        self.assertEqual(5, len(band_members_formset.forms))
        self.assertEqual('John Lennon', band_members_formset.forms[0].instance.name)

    def test_empty_formset(self):
        BandMembersFormset = childformset_factory(Band, BandMember, extra=3)
        band_members_formset = BandMembersFormset()
        self.assertEqual(3, len(band_members_formset.forms))

    def test_save_commit_false(self):
        john = BandMember(name='John Lennon')
        paul = BandMember(name='Paul McCartney')
        ringo = BandMember(name='Richard Starkey')
        beatles = Band(name='The Beatles', members=[
            john, paul, ringo
        ])
        beatles.save()
        john_id, paul_id, ringo_id = john.id, paul.id, ringo.id

        BandMembersFormset = childformset_factory(Band, BandMember, extra=3)

        band_members_formset = BandMembersFormset({
            'form-TOTAL_FORMS': 5,
            'form-INITIAL_FORMS': 3,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-DELETE': 'form-0-DELETE',
            'form-0-id': john_id,

            'form-1-name': 'Paul McCartney',
            'form-1-id': paul_id,

            'form-2-name': 'Ringo Starr',  # changing data of an existing record
            'form-2-id': ringo_id,

            'form-3-name': '',
            'form-3-id': '',

            'form-4-name': 'George Harrison',  # adding a record
            'form-4-id': '',
        }, instance=beatles)
        self.assertTrue(band_members_formset.is_valid())
        updated_members = band_members_formset.save(commit=False)

        # updated_members should only include the items that have been changed and not deleted
        self.assertEqual(2, len(updated_members))
        self.assertEqual('Ringo Starr', updated_members[0].name)
        self.assertEqual(ringo_id, updated_members[0].id)

        self.assertEqual('George Harrison', updated_members[1].name)
        self.assertEqual(None, updated_members[1].id)

        # Changes should not be committed to the db yet
        self.assertTrue(BandMember.objects.filter(name='John Lennon', id=john_id).exists())
        self.assertEqual('Richard Starkey', BandMember.objects.get(id=ringo_id).name)
        self.assertFalse(BandMember.objects.filter(name='George Harrison').exists())

        beatles.members.commit()
        # this should create/update/delete database entries
        self.assertEqual('Ringo Starr', BandMember.objects.get(id=ringo_id).name)
        self.assertTrue(BandMember.objects.filter(name='George Harrison').exists())
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

    def test_child_updates_without_ids(self):
        john = BandMember(name='John Lennon')
        beatles = Band(name='The Beatles', members=[
            john
        ])
        beatles.save()
        john_id = john.id

        paul = BandMember(name='Paul McCartney')
        beatles.members.add(paul)

        BandMembersFormset = childformset_factory(Band, BandMember, extra=3)
        band_members_formset = BandMembersFormset({
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-id': john_id,

            'form-1-name': 'Paul McCartney',  # NB no way to know programmatically that this form corresponds to the 'paul' object
            'form-1-id': '',
        }, instance=beatles)

        self.assertTrue(band_members_formset.is_valid())
        band_members_formset.save(commit=False)
        self.assertEqual(2, beatles.members.count())

    def test_max_num_ignored_in_validation_when_validate_max_false(self):
        BandMembersFormset = childformset_factory(Band, BandMember, max_num=2)

        band_members_formset = BandMembersFormset({
            'form-TOTAL_FORMS': 3,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-id': '',

            'form-1-name': 'Paul McCartney',
            'form-1-id': '',

            'form-2-name': 'Ringo Starr',
            'form-2-id': '',
        })
        self.assertTrue(band_members_formset.is_valid())

    def test_max_num_fail_validation(self):
        BandMembersFormset = childformset_factory(Band, BandMember, max_num=2, validate_max=True)

        band_members_formset = BandMembersFormset({
            'form-TOTAL_FORMS': 3,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-id': '',

            'form-1-name': 'Paul McCartney',
            'form-1-id': '',

            'form-2-name': 'Ringo Starr',
            'form-2-id': '',
        })
        self.assertFalse(band_members_formset.is_valid())
        self.assertEqual(band_members_formset.non_form_errors()[0], "Please submit 2 or fewer forms.")

    def test_max_num_pass_validation(self):
        BandMembersFormset = childformset_factory(Band, BandMember, max_num=2, validate_max=True)

        band_members_formset = BandMembersFormset({
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-id': '',

            'form-1-name': 'Paul McCartney',
            'form-1-id': '',
        })
        self.assertTrue(band_members_formset.is_valid())

    def test_min_num_ignored_in_validation_when_validate_max_false(self):
        BandMembersFormset = childformset_factory(Band, BandMember, min_num=2)

        band_members_formset = BandMembersFormset({
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-id': '',
        })
        self.assertTrue(band_members_formset.is_valid())

    def test_min_num_fail_validation(self):
        BandMembersFormset = childformset_factory(Band, BandMember, min_num=2, validate_min=True)

        band_members_formset = BandMembersFormset({
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-id': '',
        })
        self.assertFalse(band_members_formset.is_valid())
        self.assertEqual(band_members_formset.non_form_errors()[0], "Please submit 2 or more forms.")

    def test_min_num_pass_validation(self):
        BandMembersFormset = childformset_factory(Band, BandMember, min_num=2, validate_min=True)

        band_members_formset = BandMembersFormset({
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-id': '',

            'form-1-name': 'Paul McCartney',
            'form-1-id': '',
        })
        self.assertTrue(band_members_formset.is_valid())


class ChildFormsetWithM2MTest(TestCase):

    def setUp(self):
        self.james_joyce = Author.objects.create(name='James Joyce')
        self.charles_dickens = Author.objects.create(name='Charles Dickens')

        self.paper = NewsPaper.objects.create(title='the daily record')
        self.article = Article.objects.create(
            paper=self.paper,
            title='Test article',
            authors=[self.james_joyce],
        )
        ArticleFormset = childformset_factory(NewsPaper, Article, exclude=['categories', 'tags'], extra=3)
        self.formset = ArticleFormset({
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 10,

            'form-0-id': self.article.id,
            'form-0-title': self.article.title,
            'form-0-authors': [self.james_joyce.id, self.charles_dickens.id],
        }, instance=self.paper)

        ArticleTagsFormset = childformset_factory(NewsPaper, Article, exclude=['categories', 'authors'], extra=3)
        self.tags_formset = ArticleTagsFormset({
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 10,

            'form-0-id': self.article.id,
            'form-0-title': self.article.title,
            'form-0-tags': 'tag1, tagtwo',
        }, instance=self.paper)


    def test_save_with_commit_false(self):
        self.assertTrue(self.formset.is_valid())
        saved_articles = self.formset.save(commit=False)
        updated_article = saved_articles[0]

        # in memory
        self.assertIn(self.james_joyce, updated_article.authors.all())
        self.assertIn(self.charles_dickens, updated_article.authors.all())

        # in db
        db_article = Article.objects.get(id=self.article.id)
        self.assertIn(self.james_joyce, db_article.authors.all())
        self.assertNotIn(self.charles_dickens, db_article.authors.all())


    def test_save_with_commit_true(self):
        self.assertTrue(self.formset.is_valid())
        saved_articles = self.formset.save(commit=True)
        updated_article = saved_articles[0]

        # in db
        db_article = Article.objects.get(id=self.article.id)
        self.assertIn(self.james_joyce, db_article.authors.all())
        self.assertIn(self.charles_dickens, db_article.authors.all())

        # in memory
        self.assertIn(self.james_joyce, updated_article.authors.all())
        self.assertIn(self.charles_dickens, updated_article.authors.all())


    def test_tags_save_with_commit_false(self):
        self.assertTrue(self.tags_formset.is_valid())
        saved_articles = self.tags_formset.save(commit=False)
        updated_article = saved_articles[0]

        # in memory
        self.assertIn('tag1', [t.slug for t in updated_article.tags.all()])
        self.assertIn('tagtwo', [t.slug for t in updated_article.tags.all()])

        # in db
        db_article = Article.objects.get(id=self.article.id)
        self.assertNotIn('tag1', [t.slug for t in db_article.tags.all()])
        self.assertNotIn('tagtwo', [t.slug for t in db_article.tags.all()])


    def test_tags_save_with_commit_true(self):
        self.assertTrue(self.tags_formset.is_valid())
        saved_articles = self.tags_formset.save(commit=True)
        updated_article = saved_articles[0]

        # in db
        db_article = Article.objects.get(id=self.article.id)
        self.assertIn('tag1', [t.slug for t in db_article.tags.all()])
        self.assertIn('tagtwo', [t.slug for t in db_article.tags.all()])

        # in memory
        self.assertIn('tag1', [t.slug for t in updated_article.tags.all()])
        self.assertIn('tagtwo', [t.slug for t in updated_article.tags.all()])


class OrderedFormsetTest(TestCase):
    def test_saving_formset_preserves_order(self):
        AlbumsFormset = childformset_factory(Band, Album, extra=3, can_order=True)
        beatles = Band(name='The Beatles')
        albums_formset = AlbumsFormset({
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'With The Beatles',
            'form-0-id': '',
            'form-0-ORDER': '2',

            'form-1-name': 'Please Please Me',
            'form-1-id': '',
            'form-1-ORDER': '1',
        }, instance=beatles)
        self.assertTrue(albums_formset.is_valid())

        albums_formset.save(commit=False)

        album_names = [album.name for album in beatles.albums.all()]
        self.assertEqual(['Please Please Me', 'With The Beatles'], album_names)
