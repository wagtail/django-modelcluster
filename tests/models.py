from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel


@python_2_unicode_compatible
class Band(ClusterableModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class BandMember(models.Model):
    band = ParentalKey('Band', related_name='members', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['band', 'name']


@python_2_unicode_compatible
class Album(models.Model):
    band = ParentalKey('Band', related_name='albums')
    name = models.CharField(max_length=255)
    release_date = models.DateField(null=True, blank=True)
    sort_order = models.IntegerField(null=True, blank=True, editable=False)

    sort_order_field = 'sort_order'

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_order']


class TaggedPlace(TaggedItemBase):
    content_object = ParentalKey('Place', related_name='tagged_items', on_delete=models.CASCADE)


@python_2_unicode_compatible
class Place(ClusterableModel):
    name = models.CharField(max_length=255)
    tags = ClusterTaggableManager(through=TaggedPlace, blank=True)

    def __str__(self):
        return self.name


class Restaurant(Place):
    serves_hot_dogs = models.BooleanField(default=False)
    proprietor = models.ForeignKey('Chef', null=True, blank=True, on_delete=models.SET_NULL, related_name='restaurants')


class TaggedNonClusterPlace(TaggedItemBase):
    content_object = models.ForeignKey('NonClusterPlace', related_name='tagged_items', on_delete=models.CASCADE)


@python_2_unicode_compatible
class NonClusterPlace(models.Model):
    """
    For backwards compatibility we need ClusterModel to work with
    plain TaggableManagers (as opposed to ClusterTaggableManager), albeit
    without the in-memory relation behaviour
    """
    name = models.CharField(max_length=255)
    tags = TaggableManager(through=TaggedNonClusterPlace, blank=True)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Dish(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Wine(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Chef(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class MenuItem(models.Model):
    restaurant = ParentalKey('Restaurant', related_name='menu_items', on_delete=models.CASCADE)
    dish = models.ForeignKey('Dish', related_name='+', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    recommended_wine = models.ForeignKey('Wine', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    def __str__(self):
        return "%s - %f" % (self.dish, self.price)


@python_2_unicode_compatible
class Review(models.Model):
    place = ParentalKey('Place', related_name='reviews', on_delete=models.CASCADE)
    author = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return "%s on %s" % (self.author, self.place.name)


@python_2_unicode_compatible
class Log(ClusterableModel):
    time = models.DateTimeField(blank=True, null=True)
    data = models.CharField(max_length=255)

    def __str__(self):
        return "[%s] %s" % (self.time.isoformat(), self.data)


@python_2_unicode_compatible
class Document(ClusterableModel):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents')

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class NewsPaper(ClusterableModel):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class TaggedArticle(TaggedItemBase):
    content_object = ParentalKey('Article', related_name='tagged_items', on_delete=models.CASCADE)


@python_2_unicode_compatible
class Article(ClusterableModel):
    paper = ParentalKey(NewsPaper, blank=True, null=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    authors = ParentalManyToManyField('Author', related_name='articles_by_author')
    categories = ParentalManyToManyField('Category', related_name='articles_by_category')
    tags = ClusterTaggableManager(through=TaggedArticle, blank=True)

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class Author(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


@python_2_unicode_compatible
class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Gallery(ClusterableModel):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class GalleryImage(models.Model):
    gallery = ParentalKey(Gallery, related_name='images', on_delete=models.CASCADE)
    image = models.FileField()
