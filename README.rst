django-modelcluster
===================

If you had a data model like this::

 class Band(models.Model):
     name = models.CharField(max_length=255)

 class BandMember(models.Model):
     band = models.ForeignKey('Band', related_name='members')
     name = models.CharField(max_length=255)


wouldn't it be nice if you could construct bundles of objects like this, independently of the database::

 beatles = Band(name='The Beatles')
 beatles.members = [
     BandMember(name='John Lennon'),
     BandMember(name='Paul McCartney'),
 ]

Unfortunately, you can't. Objects need to exist in the database for foreign key relations to work::

 IntegrityError: null value in column "band_id" violates not-null constraint

But what if you could? There are all sorts of scenarios where you might want to work with a 'cluster' of related objects, without necessarily holding them in the database: maybe you want to render a preview of the data the user has just submitted, prior to saving. Maybe you need to construct a tree of things, serialize them and hand them off to some external system. Maybe you have a workflow where your models exist in an incomplete 'draft' state for an extended time, or you need to handle multiple revisions, and you don't want to redesign your database around that requirement.

**django-modelcluster** extends Django's foreign key relations to make this possible. It introduces a new type of relation, *ParentalKey*, where the related models are stored locally to the 'parent' model until the parent is explicitly saved. Up to that point, the related models can still be accessed through a subset of the QuerySet API::

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
