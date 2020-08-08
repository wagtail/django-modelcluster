from django.test import TestCase

from modelcluster.models import get_all_child_relations

from tests.models import Band, BandMember, Article, Author, Category


# Get child relations
band_child_rels_by_model = {
    rel.related_model: rel
    for rel in get_all_child_relations(Band)
}
band_members_rel = band_child_rels_by_model[BandMember]


class TestCopyCluster(TestCase):
    def test_can_create_cluster(self):
        beatles = Band(name='The Beatles')

        self.assertEqual(0, beatles.members.count())

        beatles.members = [
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ]
        beatles.save()

        beatles_copy, child_object_map = beatles.copy_cluster()

        # The copy should be unsaved
        self.assertIsNone(beatles_copy.pk)
        beatles_copy.save()

        # Check that both versions have the same content
        self.assertEqual(beatles.name, beatles_copy.name)
        self.assertEqual([member.name for member in beatles.members.all()], [member.name for member in beatles_copy.members.all()])

        # Check that the content has been copied
        self.assertNotEqual(beatles.pk, beatles_copy.pk)
        self.assertNotEqual([member.pk for member in beatles.members.all()], [member.pk for member in beatles_copy.members.all()])

        # Check child_object_map
        old_john = beatles.members.get(name='John Lennon')
        old_paul = beatles.members.get(name='Paul McCartney')
        new_john = beatles_copy.members.get(name='John Lennon')
        new_paul = beatles_copy.members.get(name='Paul McCartney')
        self.assertEqual(child_object_map, {
            (band_members_rel, old_john.pk): new_john,
            (band_members_rel, old_paul.pk): new_paul,
        })

    def test_copies_parental_many_to_many_fields(self):
        article = Article(title="Test Title")
        author_1 = Author.objects.create(name="Author 1")
        author_2 = Author.objects.create(name="Author 2")
        article.authors = [author_1, author_2]
        category_1 = Category.objects.create(name="Category 1")
        category_2 = Category.objects.create(name="Category 2")
        article.categories = [category_1, category_2]
        article.save()

        article_copy, child_object_map = article.copy_cluster()

        # The copy should be unsaved
        self.assertIsNone(article_copy.pk)
        article_copy.save()

        # Check that both versions have the same content
        self.assertEqual(article.title, article_copy.title)
        self.assertEqual([author.name for author in article.authors.all()], [author.name for author in article_copy.authors.all()])
        self.assertEqual([category.name for category in article.categories.all()], [category.name for category in article_copy.categories.all()])

        # Check that the content has been copied
        self.assertNotEqual(article.pk, article_copy.pk)

        # Check child_object_map
        # ParentalManyToManyField creates an invisible through table to the referenced objects
        # We don't need to care about this though since this table is usually plain
        self.assertEqual(child_object_map, {})
