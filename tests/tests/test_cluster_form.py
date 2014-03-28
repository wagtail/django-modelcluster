from __future__ import unicode_literals

from django.test import TestCase
from tests.models import Band, BandMember, Album
from modelcluster.forms import ClusterForm
from django.forms import Textarea, CharField

import datetime


class ClusterFormTest(TestCase):
    def test_cluster_form(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        self.assertTrue(BandForm.formsets)

        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])

        form = BandForm(instance=beatles)

        self.assertEqual(5, len(form.formsets['members'].forms))
        self.assertTrue('albums' in form.as_p())

    def test_empty_cluster_form(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        form = BandForm()
        self.assertEqual(3, len(form.formsets['members'].forms))

    def test_incoming_form_data(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        beatles = Band(name='The Beatles', members=[
            BandMember(name='George Harrison'),
        ])
        form = BandForm({
            'name': "The Beatles",

            'members-TOTAL_FORMS': 4,
            'members-INITIAL_FORMS': 1,
            'members-MAX_NUM_FORMS': 1000,

            'members-0-name': 'George Harrison',
            'members-0-DELETE': 'members-0-DELETE',
            'members-0-id': '',

            'members-1-name': 'John Lennon',
            'members-1-id': '',

            'members-2-name': 'Paul McCartney',
            'members-2-id': '',

            'members-3-name': '',
            'members-3-id': '',

            'albums-TOTAL_FORMS': 0,
            'albums-INITIAL_FORMS': 0,
            'albums-MAX_NUM_FORMS': 1000,
        }, instance=beatles)

        self.assertTrue(form.is_valid())
        result = form.save(commit=False)
        self.assertEqual(result, beatles)

        self.assertEqual(2, beatles.members.count())
        self.assertEqual('John Lennon', beatles.members.all()[0].name)

        # should not exist in the database yet
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

        beatles.save()
        # this should create database entries
        self.assertTrue(Band.objects.filter(name='The Beatles').exists())
        self.assertTrue(BandMember.objects.filter(name='John Lennon').exists())

    def test_explicit_formset_list(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band
                formsets = ('members',)

        form = BandForm()
        self.assertTrue(form.formsets.get('members'))
        self.assertFalse(form.formsets.get('albums'))

        self.assertTrue('members' in form.as_p())
        self.assertFalse('albums' in form.as_p())

    def test_excluded_formset_list(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band
                exclude_formsets = ('albums',)

        form = BandForm()
        self.assertTrue(form.formsets.get('members'))
        self.assertFalse(form.formsets.get('albums'))

        self.assertTrue('members' in form.as_p())
        self.assertFalse('albums' in form.as_p())

    def test_widget_overrides(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band
                widgets = {
                    'name': Textarea(),
                    'members': {
                        'name': Textarea()
                    }
                }

        form = BandForm()
        self.assertEqual(Textarea, type(form['name'].field.widget))
        self.assertEqual(Textarea, type(form.formsets['members'].forms[0]['name'].field.widget))

    def test_formfield_callback(self):

        def formfield_for_dbfield(db_field, **kwargs):
            # a particularly stupid formfield_callback that just uses Textarea for everything
            return CharField(widget=Textarea, **kwargs)

        class BandFormWithFFC(ClusterForm):
            formfield_callback = formfield_for_dbfield
            class Meta:
                model = Band

        form = BandFormWithFFC()
        self.assertEqual(Textarea, type(form['name'].field.widget))
        self.assertEqual(Textarea, type(form.formsets['members'].forms[0]['name'].field.widget))

    def test_saved_items(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        beatles.save()
        member0, member1 = beatles.members.all()
        self.assertTrue(member0.id)
        self.assertTrue(member1.id)

        form = BandForm({
            'name': "The New Beatles",

            'members-TOTAL_FORMS': 4,
            'members-INITIAL_FORMS': 2,
            'members-MAX_NUM_FORMS': 1000,

            'members-0-name': member0.name,
            'members-0-DELETE': 'members-0-DELETE',
            'members-0-id': member0.id,

            'members-1-name': member1.name,
            'members-1-id': member1.id,

            'members-2-name': 'George Harrison',
            'members-2-id': '',

            'members-3-name': '',
            'members-3-id': '',

            'albums-TOTAL_FORMS': 0,
            'albums-INITIAL_FORMS': 0,
            'albums-MAX_NUM_FORMS': 1000,
        }, instance=beatles)
        self.assertTrue(form.is_valid())
        form.save()

        new_beatles = Band.objects.get(id=beatles.id)
        self.assertEqual('The New Beatles', new_beatles.name)
        self.assertTrue(BandMember.objects.filter(name='George Harrison').exists())
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

    def test_saved_items_with_non_db_relation(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        beatles.save()
        member0, member1 = beatles.members.all()

        # pack and unpack the record so that we're working with a non-db-backed queryset
        new_beatles = Band.from_json(beatles.to_json())

        form = BandForm({
            'name': "The New Beatles",

            'members-TOTAL_FORMS': 4,
            'members-INITIAL_FORMS': 2,
            'members-MAX_NUM_FORMS': 1000,

            'members-0-name': member0.name,
            'members-0-DELETE': 'members-0-DELETE',
            'members-0-id': member0.id,

            'members-1-name': member1.name,
            'members-1-id': member1.id,

            'members-2-name': 'George Harrison',
            'members-2-id': '',

            'members-3-name': '',
            'members-3-id': '',

            'albums-TOTAL_FORMS': 0,
            'albums-INITIAL_FORMS': 0,
            'albums-MAX_NUM_FORMS': 1000,
        }, instance=new_beatles)
        self.assertTrue(form.is_valid())
        form.save()

        new_beatles = Band.objects.get(id=beatles.id)
        self.assertEqual('The New Beatles', new_beatles.name)
        self.assertTrue(BandMember.objects.filter(name='George Harrison').exists())
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

    def test_creation(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        form = BandForm({
            'name': "The Beatles",

            'members-TOTAL_FORMS': 4,
            'members-INITIAL_FORMS': 0,
            'members-MAX_NUM_FORMS': 1000,

            'members-0-name': 'John Lennon',
            'members-0-id': '',

            'members-1-name': 'Paul McCartney',
            'members-1-id': '',

            'members-2-name': 'Pete Best',
            'members-2-DELETE': 'members-0-DELETE',
            'members-2-id': '',

            'members-3-name': '',
            'members-3-id': '',

            'albums-TOTAL_FORMS': 0,
            'albums-INITIAL_FORMS': 0,
            'albums-MAX_NUM_FORMS': 1000,
        })
        self.assertTrue(form.is_valid())
        beatles = form.save()

        self.assertTrue(beatles.id)
        self.assertEqual('The Beatles', beatles.name)
        self.assertEqual('The Beatles', Band.objects.get(id=beatles.id).name)
        self.assertEqual(2, beatles.members.count())
        self.assertTrue(BandMember.objects.filter(name='John Lennon').exists())
        self.assertFalse(BandMember.objects.filter(name='Pete Best').exists())

    def test_sort_order_is_output_on_form(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        form = BandForm()
        form_html = form.as_p()
        self.assertTrue('albums-0-ORDER' in form_html)
        self.assertFalse('members-0-ORDER' in form_html)

    def test_sort_order_is_committed(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        form = BandForm({
            'name': "The Beatles",

            'members-TOTAL_FORMS': 0,
            'members-INITIAL_FORMS': 0,
            'members-MAX_NUM_FORMS': 1000,

            'albums-TOTAL_FORMS': 2,
            'albums-INITIAL_FORMS': 0,
            'albums-MAX_NUM_FORMS': 1000,

            'albums-0-name': 'With The Beatles',
            'albums-0-id': '',
            'albums-0-ORDER': 2,

            'albums-1-name': 'Please Please Me',
            'albums-1-id': '',
            'albums-1-ORDER': 1,
        })
        self.assertTrue(form.is_valid())
        beatles = form.save()

        self.assertEqual('Please Please Me', beatles.albums.all()[0].name)
        self.assertEqual('With The Beatles', beatles.albums.all()[1].name)

    def test_ignore_validation_on_deleted_items(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        please_please_me = Album(name='Please Please Me', release_date = datetime.date(1963, 3, 22))
        beatles = Band(name='The Beatles', albums=[please_please_me])
        beatles.save()

        form = BandForm({
            'name': "The Beatles",

            'members-TOTAL_FORMS': 0,
            'members-INITIAL_FORMS': 0,
            'members-MAX_NUM_FORMS': 1000,

            'albums-TOTAL_FORMS': 1,
            'albums-INITIAL_FORMS': 1,
            'albums-MAX_NUM_FORMS': 1000,

            'albums-0-name': 'With The Beatles',
            'albums-0-release_date': '1963-02-31',  # invalid date
            'albums-0-id': please_please_me.id,
            'albums-0-ORDER': 1,
        }, instance=beatles)

        self.assertFalse(form.is_valid())

        form = BandForm({
            'name': "The Beatles",

            'members-TOTAL_FORMS': 0,
            'members-INITIAL_FORMS': 0,
            'members-MAX_NUM_FORMS': 1000,

            'albums-TOTAL_FORMS': 1,
            'albums-INITIAL_FORMS': 1,
            'albums-MAX_NUM_FORMS': 1000,

            'albums-0-name': 'With The Beatles',
            'albums-0-release_date': '1963-02-31',  # invalid date
            'albums-0-id': please_please_me.id,
            'albums-0-ORDER': 1,
            'albums-0-DELETE': 'albums-0-DELETE',
        }, instance=beatles)

        self.assertTrue(form.is_valid())
        result = form.save(commit=False)
        self.assertEqual(0, beatles.albums.count())
        self.assertEqual(1, Band.objects.get(id=beatles.id).albums.count())
        beatles.save()
        self.assertEqual(0, Band.objects.get(id=beatles.id).albums.count())

    def test_cluster_form_without_formsets(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band
                formsets = ()

        beatles = Band(name='The Beatles')
        beatles.save()

        form = BandForm({
            'name': "The New Beatles",
        }, instance=beatles)

        self.assertTrue(form.is_valid())

        form.save(commit=False)

        self.assertEqual(1, Band.objects.filter(name='The Beatles').count())
        beatles.save()
        self.assertEqual(0, Band.objects.filter(name='The Beatles').count())
