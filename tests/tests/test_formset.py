from __future__ import unicode_literals

from django.test import TestCase
from modelcluster.forms import transientmodelformset_factory, childformset_factory
from tests.models import Band, BandMember

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
