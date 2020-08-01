from django.db.utils import IntegrityError
from django.test import TestCase

from modelcluster.models import get_all_child_relations

from tests.models import Album, Band, BandMember

# Get child relations
band_child_rels_by_model = {
    rel.related_model: rel
    for rel in get_all_child_relations(Band)
}
band_members_rel = band_child_rels_by_model[BandMember]
band_albums_rel = band_child_rels_by_model[Album]


class TestCopyChildRelations(TestCase):
    def setUp(self):
        self.beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])

    def test_copy_child_relations_between_unsaved_objects(self):
        # This test clones the Beatles into a new band. We haven't saved them in either the old record
        # or the new one.

        # Clone the beatle
        beatles_clone = Band(name='The Beatles 2020 comeback')

        child_object_mapping = self.beatles.copy_child_relation('members', beatles_clone)

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        self.assertIsNone(new_john.pk)
        self.assertIsNone(new_paul.pk)
        self.assertEqual(new_john.band, beatles_clone)
        self.assertEqual(new_paul.band, beatles_clone)

        # As the source is unsaved, both band members are added into a list in the key with PK None
        self.assertEqual(child_object_mapping, {
            (band_members_rel, None): [new_john, new_paul]
        })

    def test_copy_child_relations_from_saved_to_unsaved_object(self):
        # This test clones the beatles from a previously saved band/child objects.
        # The only difference here is we can return the old IDs in the mapping.

        self.beatles.save()
        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')

        beatles_clone = Band(name='The Beatles 2020 comeback')

        child_object_mapping = self.beatles.copy_child_relation('members', beatles_clone)

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        self.assertIsNone(new_john.pk)
        self.assertIsNone(new_paul.pk)
        self.assertEqual(new_john.band, beatles_clone)
        self.assertEqual(new_paul.band, beatles_clone)

        # The objects are saved in the source, so we can give each item it's own entry in the mapping
        self.assertEqual(child_object_mapping, {
            (band_members_rel, john.pk): new_john,
            (band_members_rel, paul.pk): new_paul,
        })

    def test_copy_child_relations_from_saved_and_unsaved_to_unsaved_object(self):
        # This test combines the two above tests. We save the beatles band to the database with John and Paul.
        # But we then add George and Ringo in memory. When we clone them, we have IDs for John and Paul but
        # the others are treated like the unsaved John and Paul from earlier.

        self.beatles.save()
        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')
        george = self.beatles.members.add(BandMember(name='George Harrison'))
        ringo = self.beatles.members.add(BandMember(name='Ringo Starr'))

        beatles_clone = Band(name='The Beatles 2020 comeback')

        child_object_mapping = self.beatles.copy_child_relation('members', beatles_clone)

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')
        new_george = beatles_clone.members.get(name='George Harrison')
        new_ringo = beatles_clone.members.get(name='Ringo Starr')

        self.assertIsNone(new_john.pk)
        self.assertIsNone(new_paul.pk)
        self.assertIsNone(new_george.pk)
        self.assertIsNone(new_ringo.pk)
        self.assertEqual(new_john.band, beatles_clone)
        self.assertEqual(new_paul.band, beatles_clone)
        self.assertEqual(new_george.band, beatles_clone)
        self.assertEqual(new_ringo.band, beatles_clone)

        # The objects are saved in the source, so we can give each item it's own entry in the mapping
        self.assertEqual(child_object_mapping, {
            (band_members_rel, john.pk): new_john,
            (band_members_rel, paul.pk): new_paul,
            (band_members_rel, None): [new_george, new_ringo],
        })

    def test_copy_child_relations_from_unsaved_to_saved_object(self):
        # This test copies unsaved child relations into a saved object.
        # This shouldn't commit the new child objects to the database

        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')

        beatles_clone = Band(name='The Beatles 2020 comeback')
        beatles_clone.save()

        child_object_mapping = self.beatles.copy_child_relation('members', beatles_clone)

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        self.assertIsNone(new_john.pk)
        self.assertIsNone(new_paul.pk)
        self.assertEqual(new_john.band, beatles_clone)
        self.assertEqual(new_paul.band, beatles_clone)

        self.assertEqual(child_object_mapping, {
            (band_members_rel, None): [new_john, new_paul],
        })

        # Bonus test! Let's save the clone again, and see if we can access the new PKs from child_object_mapping
        # (Django should mutate the objects we already have when we save them)
        beatles_clone.save()
        self.assertTrue(child_object_mapping[(band_members_rel, None)][0].pk)
        self.assertTrue(child_object_mapping[(band_members_rel, None)][1].pk)

    def test_copy_child_relations_between_saved_objects(self):
        # This test copies child relations between two saved objects
        # This also shouldn't commit the new child objects to the database

        self.beatles.save()
        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')

        beatles_clone = Band(name='The Beatles 2020 comeback')
        beatles_clone.save()

        child_object_mapping = self.beatles.copy_child_relation('members', beatles_clone)

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        self.assertIsNone(new_john.pk)
        self.assertIsNone(new_paul.pk)
        self.assertEqual(new_john.band, beatles_clone)
        self.assertEqual(new_paul.band, beatles_clone)

        self.assertEqual(child_object_mapping, {
            (band_members_rel, john.pk): new_john,
            (band_members_rel, paul.pk): new_paul,
        })

    def test_overwrites_existing_child_relations(self):
        # By default, the copy_child_relations should overwrite existing items
        # This is the safest option as there could be unique keys or sort_order
        # fields that might not like being duplicated in this way.

        self.beatles.save()
        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')

        beatles_clone = Band(name='The Beatles 2020 comeback')
        beatles_clone.members.add(BandMember(name='Julian Lennon'))
        beatles_clone.save()

        self.assertTrue(beatles_clone.members.filter(name='Julian Lennon').exists())

        self.beatles.copy_child_relation('members', beatles_clone)

        self.assertFalse(beatles_clone.members.filter(name='Julian Lennon').exists())

    def test_commit(self):
        # The commit parameter will instruct the method to save the child objects straight away

        self.beatles.save()
        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')

        beatles_clone = Band(name='The Beatles 2020 comeback')
        beatles_clone.save()

        child_object_mapping = self.beatles.copy_child_relation('members', beatles_clone, commit=True)

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        self.assertIsNotNone(new_john.pk)
        self.assertIsNotNone(new_paul.pk)
        self.assertEqual(new_john.band, beatles_clone)
        self.assertEqual(new_paul.band, beatles_clone)

        self.assertEqual(child_object_mapping, {
            (band_members_rel, john.pk): new_john,
            (band_members_rel, paul.pk): new_paul,
        })

    def test_commit_to_unsaved(self):
        # You can't use commit if the target isn't saved
        self.beatles.save()
        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')

        beatles_clone = Band(name='The Beatles 2020 comeback')

        with self.assertRaises(IntegrityError):
            self.beatles.copy_child_relation('members', beatles_clone, commit=True)

    def test_append(self):
        # But you can specify append=True, which appends them to the existing list

        self.beatles.save()
        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')

        beatles_clone = Band(name='The Beatles 2020 comeback')
        beatles_clone.members.add(BandMember(name='Julian Lennon'))
        beatles_clone.save()

        self.assertTrue(beatles_clone.members.filter(name='Julian Lennon').exists())

        child_object_mapping = self.beatles.copy_child_relation('members', beatles_clone, append=True)

        self.assertTrue(beatles_clone.members.filter(name='Julian Lennon').exists())

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        self.assertIsNone(new_john.pk)
        self.assertIsNone(new_paul.pk)
        self.assertEqual(new_john.band, beatles_clone)
        self.assertEqual(new_paul.band, beatles_clone)

        self.assertEqual(child_object_mapping, {
            (band_members_rel, john.pk): new_john,
            (band_members_rel, paul.pk): new_paul,
        })


class TestCopyAllChildRelations(TestCase):
    def setUp(self):
        self.beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ], albums=[
            Album(name='Please Please Me', sort_order=1),
            Album(name='With The Beatles', sort_order=2),
            Album(name='Abbey Road', sort_order=3),
        ])

    def test_copy_all_child_relations_unsaved(self):
        # Let's imagine that cloned bands own the albums of their source
        # (I'm not creative enough to come up with new album names to keep this analogy going...)

        beatles_clone = Band(name='The Beatles 2020 comeback')
        child_object_mapping = self.beatles.copy_all_child_relations(beatles_clone)

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        new_album_1 = beatles_clone.albums.get(sort_order=1)
        new_album_2 = beatles_clone.albums.get(sort_order=2)
        new_album_3 = beatles_clone.albums.get(sort_order=3)

        self.assertEqual(child_object_mapping, {
            (band_members_rel, None): [new_john, new_paul],
            (band_albums_rel, None): [new_album_1, new_album_2, new_album_3],
        })

    def test_copy_all_child_relations_saved(self):
        self.beatles.save()

        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')
        album_1 = self.beatles.albums.get(sort_order=1)
        album_2 = self.beatles.albums.get(sort_order=2)
        album_3 = self.beatles.albums.get(sort_order=3)

        beatles_clone = Band(name='The Beatles 2020 comeback')
        child_object_mapping = self.beatles.copy_all_child_relations(beatles_clone)

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        new_album_1 = beatles_clone.albums.get(sort_order=1)
        new_album_2 = beatles_clone.albums.get(sort_order=2)
        new_album_3 = beatles_clone.albums.get(sort_order=3)

        self.assertEqual(child_object_mapping, {
            (band_members_rel, john.pk): new_john,
            (band_members_rel, paul.pk): new_paul,
            (band_albums_rel, album_1.pk): new_album_1,
            (band_albums_rel, album_2.pk): new_album_2,
            (band_albums_rel, album_3.pk): new_album_3,
        })

    def test_exclude(self):
        beatles_clone = Band(name='The Beatles 2020 comeback')
        child_object_mapping = self.beatles.copy_all_child_relations(beatles_clone, exclude=['albums'])

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        self.assertFalse(beatles_clone.albums.exists())

        self.assertEqual(child_object_mapping, {
            (band_members_rel, None): [new_john, new_paul],
        })

    def test_overwrites_existing_child_relations(self):
        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')

        beatles_clone = Band(name='The Beatles 2020 comeback')
        beatles_clone.members.add(BandMember(name='Julian Lennon'))

        self.assertTrue(beatles_clone.members.filter(name='Julian Lennon').exists())

        child_object_mapping = self.beatles.copy_all_child_relations(beatles_clone)

        self.assertFalse(beatles_clone.members.filter(name='Julian Lennon').exists())

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        new_album_1 = beatles_clone.albums.get(sort_order=1)
        new_album_2 = beatles_clone.albums.get(sort_order=2)
        new_album_3 = beatles_clone.albums.get(sort_order=3)

        self.assertIsNone(new_john.pk)
        self.assertIsNone(new_paul.pk)
        self.assertEqual(new_john.band, beatles_clone)
        self.assertEqual(new_paul.band, beatles_clone)

        self.assertEqual(child_object_mapping, {
            (band_members_rel, None): [new_john, new_paul],
            (band_albums_rel, None): [new_album_1, new_album_2, new_album_3],
        })

    def test_commit(self):
        # The commit parameter will instruct the method to save the child objects straight away

        self.beatles.save()
        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')
        album_1 = self.beatles.albums.get(sort_order=1)
        album_2 = self.beatles.albums.get(sort_order=2)
        album_3 = self.beatles.albums.get(sort_order=3)

        beatles_clone = Band(name='The Beatles 2020 comeback')
        beatles_clone.save()

        child_object_mapping = self.beatles.copy_all_child_relations(beatles_clone, commit=True)

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')

        new_album_1 = beatles_clone.albums.get(sort_order=1)
        new_album_2 = beatles_clone.albums.get(sort_order=2)
        new_album_3 = beatles_clone.albums.get(sort_order=3)

        self.assertIsNotNone(new_john.pk)
        self.assertIsNotNone(new_paul.pk)
        self.assertIsNotNone(new_album_1.pk)
        self.assertIsNotNone(new_album_2.pk)
        self.assertIsNotNone(new_album_3.pk)

        self.assertEqual(new_john.band, beatles_clone)
        self.assertEqual(new_paul.band, beatles_clone)
        self.assertEqual(new_album_1.band, beatles_clone)
        self.assertEqual(new_album_2.band, beatles_clone)
        self.assertEqual(new_album_3.band, beatles_clone)

        self.assertEqual(child_object_mapping, {
            (band_members_rel, john.pk): new_john,
            (band_members_rel, paul.pk): new_paul,
            (band_albums_rel, album_1.pk): new_album_1,
            (band_albums_rel, album_2.pk): new_album_2,
            (band_albums_rel, album_3.pk): new_album_3,
        })

    def test_commit_to_unsaved(self):
        # You can't use commit if the target isn't saved
        self.beatles.save()
        john = self.beatles.members.get(name='John Lennon')
        paul = self.beatles.members.get(name='Paul McCartney')

        beatles_clone = Band(name='The Beatles 2020 comeback')

        with self.assertRaises(IntegrityError):
            self.beatles.copy_all_child_relations(beatles_clone, commit=True)

    def test_append(self):
        beatles_clone = Band(name='The Beatles 2020 comeback')
        beatles_clone.members.add(BandMember(name='Julian Lennon'))

        self.assertTrue(beatles_clone.members.filter(name='Julian Lennon').exists())

        child_object_mapping = self.beatles.copy_all_child_relations(beatles_clone, append=True)

        self.assertTrue(beatles_clone.members.filter(name='Julian Lennon').exists())

        new_john = beatles_clone.members.get(name='John Lennon')
        new_paul = beatles_clone.members.get(name='Paul McCartney')
        new_album_1 = beatles_clone.albums.get(sort_order=1)
        new_album_2 = beatles_clone.albums.get(sort_order=2)
        new_album_3 = beatles_clone.albums.get(sort_order=3)

        self.assertIsNone(new_john.pk)
        self.assertIsNone(new_paul.pk)
        self.assertEqual(new_john.band, beatles_clone)
        self.assertEqual(new_paul.band, beatles_clone)

        self.assertEqual(child_object_mapping, {
            (band_members_rel, None): [new_john, new_paul],
            (band_albums_rel, None): [new_album_1, new_album_2, new_album_3],
        })
