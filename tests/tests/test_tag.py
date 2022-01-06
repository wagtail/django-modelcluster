from __future__ import unicode_literals

import unittest

from django.test import TestCase, override_settings
from taggit import VERSION as TAGGIT_VERSION
from taggit.models import Tag
from modelcluster.forms import ClusterForm

from tests.models import NonClusterPlace, Place, TaggedPlace


class TagTest(TestCase):
    def test_can_access_tags_on_unsaved_instance(self):
        mission_burrito = Place(name='Mission Burrito')
        self.assertEqual(0, mission_burrito.tags.count())

        mission_burrito.tags.add('mexican', 'burrito')
        self.assertEqual(2, mission_burrito.tags.count())
        self.assertEqual(Tag, mission_burrito.tags.all()[0].__class__)
        self.assertTrue([tag for tag in mission_burrito.tags.all() if tag.name == 'mexican'])

        mission_burrito.save()
        self.assertEqual(2, TaggedPlace.objects.filter(content_object_id=mission_burrito.id).count())

        mission_burrito.tags.remove('burrito')
        self.assertEqual(1, mission_burrito.tags.count())
        # should not affect database until we save
        self.assertEqual(2, TaggedPlace.objects.filter(content_object_id=mission_burrito.id).count())
        mission_burrito.save()
        self.assertEqual(1, TaggedPlace.objects.filter(content_object_id=mission_burrito.id).count())

        mission_burrito.tags.clear()
        self.assertEqual(0, mission_burrito.tags.count())
        # should not affect database until we save
        self.assertEqual(1, TaggedPlace.objects.filter(content_object_id=mission_burrito.id).count())
        mission_burrito.save()
        self.assertEqual(0, TaggedPlace.objects.filter(content_object_id=mission_burrito.id).count())

        if TAGGIT_VERSION >= (2, 0):
            mission_burrito.tags.set(['mexican', 'burrito'])
        else:
            mission_burrito.tags.set('mexican', 'burrito')
        self.assertEqual(2, mission_burrito.tags.count())
        self.assertEqual(0, TaggedPlace.objects.filter(content_object_id=mission_burrito.id).count())
        mission_burrito.save()
        self.assertEqual(2, TaggedPlace.objects.filter(content_object_id=mission_burrito.id).count())

    def test_prefetch_tags_doesnt_break(self):
        mission_burrito = Place(name='Mission Burrito')
        mission_burrito.tags.add('mexican', 'burrito')
        mission_burrito.save()

        atomic_burger = Place(name='Atomic Burger')
        atomic_burger.tags.add('burger')
        atomic_burger.save()

        places = list(Place.objects.order_by('name').prefetch_related('tags'))
        self.assertEqual(places[0].name, 'Atomic Burger')
        self.assertEqual(places[0].tags.first().name, 'burger')

    @unittest.expectedFailure
    def test_prefetch_tags_actually_prefetches(self):
        mission_burrito = Place(name='Mission Burrito')
        mission_burrito.tags.add('mexican', 'burrito')
        mission_burrito.save()

        atomic_burger = Place(name='Atomic Burger')
        atomic_burger.tags.add('burger')
        atomic_burger.save()

        with self.assertNumQueries(2):
            places = list(Place.objects.order_by('name').prefetch_related('tags'))
            self.assertEqual(places[0].name, 'Atomic Burger')
            self.assertEqual(places[0].tags.first().name, 'burger')

    def test_tag_form_field(self):
        class PlaceForm(ClusterForm):
            class Meta:
                model = Place
                exclude_formsets = ['tagged_items', 'reviews']
                fields = ['name', 'tags']

        mission_burrito = Place(name='Mission Burrito')
        mission_burrito.tags.add('mexican', 'burrito')

        form = PlaceForm(instance=mission_burrito)
        self.assertEqual(2, len(form['tags'].value()))
        expected_instance = TaggedPlace if TAGGIT_VERSION < (1,) else Tag
        self.assertEqual(expected_instance, form['tags'].value()[0].__class__)

        form = PlaceForm({
            'name': "Mission Burrito",
            'tags': "burrito, fajita"
        }, instance=mission_burrito)
        self.assertTrue(form.is_valid())
        mission_burrito = form.save(commit=False)
        self.assertTrue(Tag.objects.get(name='burrito') in mission_burrito.tags.all())
        self.assertTrue(Tag.objects.get(name='fajita') in mission_burrito.tags.all())
        self.assertFalse(Tag.objects.get(name='mexican') in mission_burrito.tags.all())

    def test_create_with_tags(self):
        class PlaceForm(ClusterForm):
            class Meta:
                model = Place
                exclude_formsets = ['tagged_items', 'reviews']
                fields = ['name', 'tags']

        form = PlaceForm({
            'name': "Mission Burrito",
            'tags': "burrito, fajita"
        }, instance=Place())
        self.assertTrue(form.is_valid())
        mission_burrito = form.save()
        reloaded_mission_burrito = Place.objects.get(pk=mission_burrito.pk)
        self.assertEqual(
            set(reloaded_mission_burrito.tags.all()),
            set([Tag.objects.get(name='burrito'), Tag.objects.get(name='fajita')])
        )

    def test_create_with_tags_with_plain_taggable_manager(self):
        class PlaceForm(ClusterForm):
            class Meta:
                model = NonClusterPlace
                exclude_formsets = ['tagged_items', 'reviews']
                fields = ['name', 'tags']

        form = PlaceForm({
            'name': "Mission Burrito",
            'tags': "burrito, fajita"
        }, instance=NonClusterPlace())
        self.assertTrue(form.is_valid())
        mission_burrito = form.save()
        reloaded_mission_burrito = NonClusterPlace.objects.get(pk=mission_burrito.pk)
        self.assertEqual(
            set(reloaded_mission_burrito.tags.all()),
            set([Tag.objects.get(name='burrito'), Tag.objects.get(name='fajita')])
        )

    def test_render_tag_form(self):
        class PlaceForm(ClusterForm):
            class Meta:
                model = Place
                exclude_formsets = ['tagged_items', 'reviews']
                fields = ['name', 'tags']

        mission_burrito = Place(name="Mission Burrito")
        mission_burrito.tags.add('burrito', 'mexican')
        form = PlaceForm(instance=mission_burrito)
        form_html = form.as_p()
        self.assertInHTML('<input type="text" name="tags" value="burrito, mexican" id="id_tags">', form_html)

    @override_settings(TAGGIT_CASE_INSENSITIVE=True)
    def test_case_insensitive_tags(self):
        mission_burrito = Place(name='Mission Burrito')
        mission_burrito.tags.add('burrito')
        mission_burrito.tags.add('Burrito')

        self.assertEqual(1, mission_burrito.tags.count())

    def test_integers(self):
        """Adding an integer as a tag should raise a ValueError"""
        mission_burrito = Place(name='Mission Burrito')
        with self.assertRaisesRegex(ValueError, (
                r"Cannot add 1 \(<(type|class) 'int'>\). "
                r"Expected <class 'django.db.models.base.ModelBase'> or str.")):
            mission_burrito.tags.add(1)
