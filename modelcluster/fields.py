from __future__ import unicode_literals

import django
from django.core import checks
from django.db import IntegrityError, router
from django.db.models.fields.related import ForeignKey
from django.utils.functional import cached_property

try:
    from django.db.models.fields.related import ReverseManyToOneDescriptor
except ImportError:
    # Django 1.8 and below
    from django.db.models.fields.related import ForeignRelatedObjectsDescriptor as ReverseManyToOneDescriptor


from modelcluster.utils import sort_by_fields

from modelcluster.queryset import FakeQuerySet
from modelcluster.models import ClusterableModel


def create_deferring_foreign_related_manager(related, original_manager_cls):
    """
    Create a DeferringRelatedManager class that wraps an ordinary RelatedManager
    with 'deferring' behaviour: any updates to the object set (via e.g. add() or clear())
    are written to a holding area rather than committed to the database immediately.
    Writing to the database is deferred until the model is saved.
    """

    relation_name = related.get_accessor_name()
    rel_field = related.field
    rel_model = related.related_model
    superclass = rel_model._default_manager.__class__

    class DeferringRelatedManager(superclass):
        def __init__(self, instance):
            super(DeferringRelatedManager, self).__init__()
            self.model = rel_model
            self.instance = instance

        def get_live_query_set(self):
            # deprecated; renamed to get_live_queryset to match the move from
            # get_query_set to get_queryset in Django 1.6
            return self.get_live_queryset()

        def get_live_queryset(self):
            """
            return the original manager's queryset, which reflects the live database
            """
            return original_manager_cls(self.instance).get_queryset()

        def get_queryset(self):
            """
            return the current object set with any updates applied,
            wrapped up in a FakeQuerySet if it doesn't match the database state
            """
            try:
                results = self.instance._cluster_related_objects[relation_name]
            except (AttributeError, KeyError):
                return self.get_live_queryset()

            return FakeQuerySet(related.related_model, results)

        def get_prefetch_queryset(self, instances, queryset=None):
            if queryset is None:
                db = self._db or router.db_for_read(self.model, instance=instances[0])
                queryset = super(DeferringRelatedManager, self).get_queryset().using(db)

            rel_obj_attr = rel_field.get_local_related_value
            instance_attr = rel_field.get_foreign_related_value
            instances_dict = dict((instance_attr(inst), inst) for inst in instances)

            query = {'%s__in' % rel_field.name: instances}
            qs = queryset.filter(**query)
            # Since we just bypassed this class' get_queryset(), we must manage
            # the reverse relation manually.
            for rel_obj in qs:
                instance = instances_dict[rel_obj_attr(rel_obj)]
                setattr(rel_obj, rel_field.name, instance)
            cache_name = rel_field.related_query_name()
            return qs, rel_obj_attr, instance_attr, False, cache_name

        def get_object_list(self):
            """
            return the mutable list that forms the current in-memory state of
            this relation. If there is no such list (i.e. the manager is returning
            querysets from the live database instead), one is created, populating it
            with the live database state
            """
            try:
                cluster_related_objects = self.instance._cluster_related_objects
            except AttributeError:
                cluster_related_objects = {}
                self.instance._cluster_related_objects = cluster_related_objects

            try:
                object_list = cluster_related_objects[relation_name]
            except KeyError:
                object_list = list(self.get_live_queryset())
                cluster_related_objects[relation_name] = object_list

            return object_list

        def add(self, *new_items):
            """
            Add the passed items to the stored object set, but do not commit them
            to the database
            """
            items = self.get_object_list()

            # Rule for checking whether an item in the list matches one of our targets.
            # We can't do this with a simple 'in' check due to https://code.djangoproject.com/ticket/18864 -
            # instead, we consider them to match IF:
            # - they are exactly the same Python object (by reference), or
            # - they have a non-null primary key that matches
            def items_match(item, target):
                return (item is target) or (item.pk == target.pk and item.pk is not None)

            for target in new_items:
                item_matched = False
                for i, item in enumerate(items):
                    if items_match(item, target):
                        # Replace the matched item with the new one. This ensures that any
                        # modifications to that item's fields take effect within the recordset -
                        # i.e. we can perform a virtual UPDATE to an object in the list
                        # by calling add(updated_object). Which is semantically a bit dubious,
                        # but it does the job...
                        items[i] = target
                        item_matched = True
                        break
                if not item_matched:
                    items.append(target)

                # update the foreign key on the added item to point back to the parent instance
                setattr(target, related.field.name, self.instance)

            # Sort list
            if rel_model._meta.ordering and len(items) > 1:
                sort_by_fields(items, rel_model._meta.ordering)

        def remove(self, *items_to_remove):
            """
            Remove the passed items from the stored object set, but do not commit the change
            to the database
            """
            items = self.get_object_list()

            # Rule for checking whether an item in the list matches one of our targets.
            # We can't do this with a simple 'in' check due to https://code.djangoproject.com/ticket/18864 -
            # instead, we consider them to match IF:
            # - they are exactly the same Python object (by reference), or
            # - they have a non-null primary key that matches
            def items_match(item, target):
                return (item is target) or (item.pk == target.pk and item.pk is not None)

            for target in items_to_remove:
                # filter items list in place: see http://stackoverflow.com/a/1208792/1853523
                items[:] = [item for item in items if not items_match(item, target)]

        def create(self, **kwargs):
            items = self.get_object_list()
            new_item = related.related_model(**kwargs)
            items.append(new_item)
            return new_item

        def clear(self):
            """
            Clear the stored object set, without affecting the database
            """
            try:
                cluster_related_objects = self.instance._cluster_related_objects
            except AttributeError:
                cluster_related_objects = {}
                self.instance._cluster_related_objects = cluster_related_objects

            cluster_related_objects[relation_name] = []

        def commit(self):
            """
            Apply any changes made to the stored object set to the database.
            Any objects removed from the initial set will be deleted entirely
            from the database.
            """
            if not self.instance.pk:
                raise IntegrityError("Cannot commit relation %r on an unsaved model" % relation_name)

            try:
                final_items = self.instance._cluster_related_objects[relation_name]
            except (AttributeError, KeyError):
                # _cluster_related_objects entry never created => no changes to make
                return

            original_manager = original_manager_cls(self.instance)

            live_items = list(original_manager.get_queryset())
            for item in live_items:
                if item not in final_items:
                    item.delete()

            for item in final_items:
                if django.VERSION >= (1, 9):
                    # Django 1.9+ bulk updates items by default which assumes
                    # that they have already been saved to the database.
                    # Disable this behaviour.
                    # https://code.djangoproject.com/ticket/18556
                    # https://github.com/django/django/commit/adc0c4fbac98f9cb975e8fa8220323b2de638b46
                    original_manager.add(item, bulk=False)
                else:
                    original_manager.add(item)

            # purge the _cluster_related_objects entry, so we switch back to live SQL
            del self.instance._cluster_related_objects[relation_name]

    return DeferringRelatedManager


class ChildObjectsDescriptor(ReverseManyToOneDescriptor):
    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        return self.child_object_manager_cls(instance)

    def __set__(self, instance, value):
        manager = self.__get__(instance)
        manager.clear()
        manager.add(*value)

    @cached_property
    def child_object_manager_cls(self):
        try:
            rel = self.rel
        except AttributeError:
            # Django 1.8 and below
            rel = self.related

        return create_deferring_foreign_related_manager(rel, self.related_manager_cls)


class ParentalKey(ForeignKey):
    related_accessor_class = ChildObjectsDescriptor

    # Django 1.8 has a check to prevent unsaved instances being assigned to
    # ForeignKeys. Disable it
    # This check was moved to the save() method in Django 1.8.4
    allow_unsaved_instance_assignment = True

    def contribute_to_related_class(self, cls, related):
        super(ParentalKey, self).contribute_to_related_class(cls, related)

        # store this as a child field in meta. NB child_relations only contains relations
        # defined to this specific model, not its superclasses
        try:
            cls._meta.child_relations.append(related)
        except AttributeError:
            cls._meta.child_relations = [related]

    def check(self, **kwargs):
        errors = super(ParentalKey, self).check(**kwargs)

        # Check that the destination model is a subclass of ClusterableModel.
        # If self.rel.to is a string at this point, it means that Django has been unable
        # to resolve it as a model name; if so, skip this test so that Django's own
        # system checks can report the appropriate error
        if isinstance(self.rel.to, type) and not issubclass(self.rel.to, ClusterableModel):
            errors.append(
                checks.Error(
                    'ParentalKey must point to a subclass of ClusterableModel.',
                    hint='Change {model_name} into a ClusterableModel or use a ForeignKey instead.'.format(
                        model_name=self.rel.to._meta.app_label + '.' + self.rel.to.__name__,
                    ),
                    obj=self,
                    id='modelcluster.E001',
                )
            )

        # ParentalKeys must have an accessor name (#49)
        if self.rel.get_accessor_name() == '+':
            errors.append(
                checks.Error(
                    "related_name='+' is not allowed on ParentalKey fields",
                    hint="Either change it to a valid name or remove it",
                    obj=self,
                    id='modelcluster.E002',
                )
            )

        return errors
