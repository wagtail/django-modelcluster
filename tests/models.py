from __future__ import unicode_literals

import base64

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.six import text_type

from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel


@python_2_unicode_compatible
class Band(ClusterableModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class BandMember(models.Model):
    band = ParentalKey('Band', related_name='members')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


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
    content_object = ParentalKey('Place', related_name='tagged_items')


@python_2_unicode_compatible
class Place(ClusterableModel):
    name = models.CharField(max_length=255)
    tags = ClusterTaggableManager(through=TaggedPlace, blank=True)

    def __str__(self):
        return self.name


class Restaurant(Place):
    serves_hot_dogs = models.BooleanField(default=False)
    proprietor = models.ForeignKey('Chef', null=True, blank=True, on_delete=models.SET_NULL, related_name='restaurants')


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
    restaurant = ParentalKey('Restaurant', related_name='menu_items')
    dish = models.ForeignKey('Dish', related_name='+')
    price = models.DecimalField(max_digits=6, decimal_places=2)
    recommended_wine = models.ForeignKey('Wine', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    def __str__(self):
        return "%s - %f" % (self.dish, self.price)


@python_2_unicode_compatible
class Review(models.Model):
    place = ParentalKey('Place', related_name='reviews')
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
class FooValue(object):
    value = None
    
    def __init__(self, value):
        super(FooValue, self).__init__()
        self.value = int(value)

    def __str__(self):
        return text_type(base64.b64encode(text_type(self.value).encode("utf-8")).strip())
    
    def __int__(self):
        return self.value


class FooField(models.IntegerField):
    def get_prep_value(self, value):
        if isinstance(value, FooValue):
            value = int(value)
        return value
    
    def get_db_prep_value(self, *args, **kwargs):
        value = super(FooField, self).get_db_prep_value(*args, **kwargs)
        if isinstance(value, FooValue):
            value = int(value)
        return value
    
    def to_python(self, value):
        if value is not None and not isinstance(value, FooValue):
            value = FooValue(value)
        return value
    
    def from_db_value(self, value, expression, connection, context):
        if not isinstance(value, FooValue):
            value = FooValue(value)
        return value


@python_2_unicode_compatible
class FooModel(models.Model):
    id = FooField(primary_key=True)

    def __str__(self):
        return text_type("{} instance, id {}".format(self.__class__, self.id))

class BarModel(models.Model):
    id = models.OneToOneField(FooModel, primary_key=True)

