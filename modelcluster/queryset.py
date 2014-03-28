from __future__ import unicode_literals

from django.db.models import Model

# Constructor for test functions that determine whether an object passes some boolean condition
def test_exact(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    # convert value to the correct python type for this field
    typed_value = field.to_python(value)
    if isinstance(typed_value, Model):
        if typed_value.pk is None:
            # comparing against an unsaved model, so objects need to match by reference
            return lambda obj: getattr(obj, attribute_name) is typed_value
        else:
            # comparing against a saved model; objects need to match by type and ID.
            # Additionally, where model inheritance is involved, we need to treat it as a
            # positive match if one is a subclass of the other
            def _test(obj):
                other_value = getattr(obj, attribute_name)
                if not (isinstance(typed_value, other_value.__class__) or isinstance(other_value, typed_value.__class__)):
                    return False
                return typed_value.pk == other_value.pk
            return _test
    else:
        # just a plain Python value = do a normal equality check
        return lambda obj: getattr(obj, attribute_name) == typed_value

class FakeQuerySet(object):
    def __init__(self, model, results):
        self.model = model
        self.results = results

    def all(self):
        return self

    def filter(self, **kwargs):
        filters = []  # a list of test functions; objects must pass all tests to be included
            # in the filtered list
        for key, val in kwargs.items():
            key_clauses = key.split('__')
            if len(key_clauses) != 1:
                raise NotImplementedError("Complex filters with double-underscore clauses are not implemented yet")

            filters.append(test_exact(self.model, key_clauses[0], val))

        filtered_results = [
            obj for obj in self.results
            if all([test(obj) for test in filters])
        ]

        return FakeQuerySet(self.model, filtered_results)

    def get(self, **kwargs):
        results = self.filter(**kwargs)
        result_count = results.count()

        if result_count == 0:
            raise self.model.DoesNotExist("%s matching query does not exist." % self.model._meta.object_name)
        elif result_count == 1:
            return results[0]
        else:
            raise self.model.MultipleObjectsReturned(
                "get() returned more than one %s -- it returned %s!" % (self.model._meta.object_name, result_count)
            )

    def count(self):
        return len(self.results)

    def select_related(self, *args):
        # has no meaningful effect on non-db querysets
        return self

    def values_list(self, *fields, **kwargs):
        # FIXME: values_list should return an object that behaves like both a queryset and a list,
        # so that we can do things like Foo.objects.values_list('id').order_by('id')

        flat = kwargs.get('flat')  # TODO: throw TypeError if other kwargs are present

        if not fields:
            # return a tuple of all fields
            field_names = [field.name for field in self.model._meta.fields]
            return [
                tuple([getattr(obj, field_name) for field_name in field_names])
                for obj in self.results
            ]

        if flat:
            if len(fields) > 1:
                raise TypeError("'flat' is not valid when values_list is called with more than one field.")
            field_name = fields[0]
            return [getattr(obj, field_name) for obj in self.results]
        else:
            return [
                tuple([getattr(obj, field_name) for field_name in fields])
                for obj in self.results
            ]

    def __getitem__(self, k):
        return self.results[k]

    def __iter__(self):
        return self.results.__iter__()

    def __nonzero__(self):
        return bool(self.results)

    def __repr__(self):
        return repr(list(self))

    def __len__(self):
        return len(self.results)

    ordered = True  # results are returned in a consistent order
