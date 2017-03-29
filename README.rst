.. image:: https://travis-ci.org/wagtail/django-modelcluster.svg?branch=master
    :target: https://travis-ci.org/wagtail/django-modelcluster

django-modelcluster
===================

If you had a data model like this:

.. code-block:: python

 class Band(models.Model):
     name = models.CharField(max_length=255)

 class BandMember(models.Model):
     band = models.ForeignKey('Band', related_name='members')
     name = models.CharField(max_length=255)


wouldn't it be nice if you could construct bundles of objects like this, independently of the database:

.. code-block:: python

 beatles = Band(name='The Beatles')
 beatles.members = [
     BandMember(name='John Lennon'),
     BandMember(name='Paul McCartney'),
 ]

Unfortunately, you can't. Objects need to exist in the database for foreign key relations to work:

.. code-block:: python

 IntegrityError: null value in column "band_id" violates not-null constraint

But what if you could? There are all sorts of scenarios where you might want to work with a 'cluster' of related objects, without necessarily holding them in the database: maybe you want to render a preview of the data the user has just submitted, prior to saving. Maybe you need to construct a tree of things, serialize them and hand them off to some external system. Maybe you have a workflow where your models exist in an incomplete 'draft' state for an extended time, or you need to handle multiple revisions, and you don't want to redesign your database around that requirement.

**django-modelcluster** extends Django's foreign key relations to make this possible. It introduces a new type of relation, *ParentalKey*, where the related models are stored locally to the 'parent' model until the parent is explicitly saved. Up to that point, the related models can still be accessed through a subset of the QuerySet API:

.. code-block:: python
 
 from modelcluster.models import ClusterableModel
 from modelcluster.fields import ParentalKey
 
 
 class Band(ClusterableModel):
     name = models.CharField(max_length=255)

 class BandMember(models.Model):
     band = ParentalKey('Band', related_name='members')
     name = models.CharField(max_length=255)


 >>> beatles = Band(name='The Beatles')
 >>> beatles.members = [
 ...     BandMember(name='John Lennon'),
 ...     BandMember(name='Paul McCartney'),
 ... ]
 >>> [member.name for member in beatles.members.all()]
 ['John Lennon', 'Paul McCartney']
 >>> beatles.members.add(BandMember(name='George Harrison'))
 >>> beatles.members.count()
 3
 >>> beatles.save()  # only now are the records written to the database

For more examples, see the unit tests.


Many-to-many relations
----------------------

For many-to-many relations, a corresponding *ParentalManyToManyField* is available:

.. code-block:: python

 from modelcluster.models import ClusterableModel
 from modelcluster.fields import ParentalManyToManyField

 class Movie(ClusterableModel):
     title = models.CharField(max_length=255)
     actors = ParentalManyToManyField('Actor', related_name='movies')

 class Actor(models.Model):
     name = models.CharField(max_length=255)


 >>> harrison_ford = Actor.objects.create(name='Harrison Ford')
 >>> carrie_fisher = Actor.objects.create(name='Carrie Fisher')
 >>> star_wars = Movie(title='Star Wars')
 >>> star_wars.actors = [harrison_ford, carrie_fisher]
 >>> blade_runner = Movie(title='Blade Runner')
 >>> blade_runner.actors.add(harrison_ford)
 >>> star_wars.actors.count()
 2
 >>> [movie.title for movie in harrison_ford.movies.all()]  # the Movie records are not in the database yet
 []
 >>> star_wars.save()  # Star Wars now exists in the database (along with the 'actor' relations)
 >>> [movie.title for movie in harrison_ford.movies.all()]
 ['Star Wars']

Note that ``ParentalManyToManyField`` is defined on the parent model rather than the related model, just as a standard ``ManyToManyField`` would be. Also note that the related objects - the ``Actor`` instances in the above example - must exist in the database before being associated with the parent record. (The ``ParentalManyToManyField`` allows the relations between Movies and Actors to be stored in memory without writing to the database, but not the ``Actor`` records themselves.)


Introspection
-------------
If you need to find out which child relations exist on a parent model - to create a deep copy of the model and all its children, say - use the ``modelcluster.models.get_all_child_relations`` function:

.. code-block:: python

 >>> from modelcluster.models import get_all_child_relations
 >>> get_all_child_relations(Band)
 [<RelatedObject: tests:bandmember related to band>, <RelatedObject: tests:album related to band>]

This includes relations that are defined on any superclasses of the parent model.

To retrieve a list of all ParentalManyToManyFields defined on a parent model, use ``modelcluster.models.get_all_child_m2m_relations``:

.. code-block:: python

 >>> from modelcluster.models import get_all_child_m2m_relations
 >>> get_all_child_m2m_relations(Movie)
 [<modelcluster.fields.ParentalManyToManyField: actors>]
