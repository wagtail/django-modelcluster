from django.db import models

from modelcluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel


class Band(ClusterableModel):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class BandMember(models.Model):
    band = ParentalKey('Band', related_name='members')
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Album(models.Model):
    band = ParentalKey('Band', related_name='albums')
    name = models.CharField(max_length=255)
    release_date = models.DateField(null=True, blank=True)
    sort_order = models.IntegerField(null=True, blank=True, editable=False)

    sort_order_field = 'sort_order'

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['sort_order']


class TaggedPlace(TaggedItemBase):
    content_object = ParentalKey('Place', related_name='tagged_items')

class Place(ClusterableModel):
    name = models.CharField(max_length=255)
    tags = ClusterTaggableManager(through=TaggedPlace)

    def __unicode__(self):
        return self.name

class Restaurant(Place):
    serves_hot_dogs = models.BooleanField()
    proprietor = models.ForeignKey('Chef', null=True, blank=True, on_delete=models.SET_NULL, related_name='restaurants')

class Dish(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class Wine(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class Chef(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class MenuItem(models.Model):
    restaurant = ParentalKey('Restaurant', related_name='menu_items')
    dish = models.ForeignKey('Dish', related_name='+')
    price = models.DecimalField(max_digits=6, decimal_places=2)
    recommended_wine = models.ForeignKey('Wine', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    def __unicode__(self):
        return "%s - %f" % (self.dish, self.price)
