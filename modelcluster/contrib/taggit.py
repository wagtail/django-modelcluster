from __future__ import unicode_literals
from __future__ import absolute_import

from django.conf import settings
from django.utils import six
from taggit.managers import TaggableManager, _TaggableManager
from taggit.utils import require_instance_manager

from modelcluster.queryset import FakeQuerySet


class _ClusterTaggableManager(_TaggableManager):
    @require_instance_manager
    def get_tagged_item_manager(self):
        """Return the manager that handles the relation from this instance to the tagged_item class.
        If content_object on the tagged_item class is defined as a ParentalKey, this will be a
        DeferringRelatedManager which allows writing related objects without committing them
        to the database.
        """
        rel_name = self.through._meta.get_field('content_object').rel.get_accessor_name()
        return getattr(self.instance, rel_name)

    def get_queryset(self, extra_filters=None):
        if self.instance is None:
            # this manager is not associated with a specific model instance
            # (which probably means it's being invoked within a prefetch_related operation);
            # this means that we don't have to deal with uncommitted models/tags, and can just
            # use the standard taggit handler
            return super(_ClusterTaggableManager, self).get_queryset(extra_filters)
        else:
            # FIXME: we ought to have some way of querying the tagged item manager about whether
            # it has uncommitted changes, and return a real queryset (using the original taggit logic)
            # if not
            return FakeQuerySet(
                self.through.tag_model(),
                [tagged_item.tag for tagged_item in self.get_tagged_item_manager().all()]
            )

    @require_instance_manager
    def add(self, *tags):
        # Add `tags` (which may be either strings or tag objects) to this instance's tag list.

        # This implementation is a copy of taggit's own logic from _TaggableManager.add
        # except for the final part that creates the 'through' objects (where we need to
        # push them to the tagged_item manager, rather than creating them as DB objects).
        # This is currently in sync with django-taggit master as of 2016-04-26:
        # https://github.com/alex/django-taggit/tree/1daae6fc83009ef86cc62445537746a08aab91aa

        # First turn the 'tags' list (which may be a mixture of tag objects and
        # strings which may or may not correspond to existing tag objects)
        # into 'tag_objs', a set of tag objects
        str_tags = set()
        tag_objs = set()
        for t in tags:
            if isinstance(t, self.through.tag_model()):
                tag_objs.add(t)
            elif isinstance(t, six.string_types):
                str_tags.add(t)
            else:
                raise ValueError("Cannot add {0} ({1}). Expected {2} or str.".format(
                    t, type(t), type(self.through.tag_model())))

        if getattr(settings, 'TAGGIT_CASE_INSENSITIVE', False):
            # Some databases can do case-insensitive comparison with IN, which
            # would be faster, but we can't rely on it or easily detect it.
            existing = []
            tags_to_create = []

            for name in str_tags:
                try:
                    tag = self.through.tag_model().objects.get(name__iexact=name)
                    existing.append(tag)
                except self.through.tag_model().DoesNotExist:
                    tags_to_create.append(name)
        else:
            # If str_tags has 0 elements Django actually optimizes that to not do a
            # query.  Malcolm is very smart.
            existing = self.through.tag_model().objects.filter(
                name__in=str_tags
            )

            tags_to_create = str_tags - set(t.name for t in existing)

        tag_objs.update(existing)

        for new_tag in tags_to_create:
            tag_objs.add(self.through.tag_model().objects.create(name=new_tag))

        # Now write these to the relation
        tagged_item_manager = self.get_tagged_item_manager()
        for tag in tag_objs:
            if not tagged_item_manager.filter(tag=tag):
                # make an instance of the self.through model and add it to the relation
                tagged_item = self.through(tag=tag)
                tagged_item_manager.add(tagged_item)

    @require_instance_manager
    def remove(self, *tags):
        tagged_item_manager = self.get_tagged_item_manager()
        tagged_items = [
            tagged_item for tagged_item in tagged_item_manager.all()
            if tagged_item.tag.name in tags
        ]
        tagged_item_manager.remove(*tagged_items)

    @require_instance_manager
    def clear(self):
        self.get_tagged_item_manager().clear()


class ClusterTaggableManager(TaggableManager):
    def __get__(self, instance, model):
        # override TaggableManager's requirement for instance to have a primary key
        # before we can access its tags
        try:
            manager = _ClusterTaggableManager(
                through=self.through, model=model, instance=instance, prefetch_cache_name=self.name
            )
        except TypeError:  # fallback for django-taggit pre 0.11
            manager = _ClusterTaggableManager(
                through=self.through, model=model, instance=instance
            )

        return manager

    def value_from_object(self, instance):
        # retrieve the queryset via the related manager on the content object,
        # to accommodate the possibility of this having uncommitted changes relative to
        # the live database
        rel_name = self.through._meta.get_field('content_object').rel.get_accessor_name()
        return getattr(instance, rel_name).all()
