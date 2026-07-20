from __future__ import unicode_literals

import inspect
import logging
import re

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model, Q, prefetch_related_objects

from modelcluster.utils import (
    NullRelationshipValueEncountered,
    extract_field_value,
    get_model_field,
    sort_by_fields,
)


# Constructor for test functions that determine whether an object passes some boolean condition
def test_exact(model, attribute_name, value):
    if isinstance(value, Model):
        if value.pk is None:
            # comparing against an unsaved model, so objects need to match by reference
            def _test(obj):
                try:
                    other_value = extract_field_value(obj, attribute_name)
                except NullRelationshipValueEncountered:
                    return False
                return other_value is value

            return _test

        else:
            # comparing against a saved model; objects need to match by type and ID.
            # Additionally, where model inheritance is involved, we need to treat it as a
            # positive match if one is a subclass of the other
            def _test(obj):
                try:
                    other_value = extract_field_value(obj, attribute_name)
                except NullRelationshipValueEncountered:
                    return False
                return value.pk == other_value.pk and (
                    isinstance(value, other_value.__class__)
                    or isinstance(other_value, value.__class__)
                )

            return _test
    else:
        field = get_model_field(model, attribute_name)
        # convert value to the correct python type for this field
        typed_value = field.to_python(value)

        # just a plain Python value = do a normal equality check
        def _test(obj):
            try:
                other_value = extract_field_value(obj, attribute_name)
            except NullRelationshipValueEncountered:
                return False
            return other_value == typed_value

        return _test


def test_iexact(model, attribute_name, match_value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(match_value)

    if match_value is None:

        def _test(obj):
            try:
                val = extract_field_value(obj, attribute_name)
            except NullRelationshipValueEncountered:
                return False
            return val is None
    else:
        match_value = match_value.upper()

        def _test(obj):
            try:
                val = extract_field_value(obj, attribute_name)
            except NullRelationshipValueEncountered:
                return False
            return val is not None and val.upper() == match_value

    return _test


def test_contains(model, attribute_name, value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and match_value in val

    return _test


def test_icontains(model, attribute_name, value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(value).upper()

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and match_value in val.upper()

    return _test


def test_lt(model, attribute_name, value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and val < match_value

    return _test


def test_lte(model, attribute_name, value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and val <= match_value

    return _test


def test_gt(model, attribute_name, value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and val > match_value

    return _test


def test_gte(model, attribute_name, value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and val >= match_value

    return _test


def test_in(model, attribute_name, value_list):
    field = get_model_field(model, attribute_name)
    match_values = set(field.to_python(val) for val in value_list)

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val in match_values

    return _test


def test_startswith(model, attribute_name, value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and val.startswith(match_value)

    return _test


def test_istartswith(model, attribute_name, value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(value).upper()

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and val.upper().startswith(match_value)

    return _test


def test_endswith(model, attribute_name, value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and val.endswith(match_value)

    return _test


def test_iendswith(model, attribute_name, value):
    field = get_model_field(model, attribute_name)
    match_value = field.to_python(value).upper()

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and val.upper().endswith(match_value)

    return _test


def test_range(model, attribute_name, range_val):
    field = get_model_field(model, attribute_name)
    start_val = field.to_python(range_val[0])
    end_val = field.to_python(range_val[1])

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and val >= start_val and val <= end_val

    return _test


def test_isnull(model, attribute_name, sense):
    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        if sense:
            return val is None
        else:
            return val is not None

    return _test


def test_regex(model, attribute_name, regex_string):
    regex = re.compile(regex_string)

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and regex.search(val)

    return _test


def test_iregex(model, attribute_name, regex_string):
    regex = re.compile(regex_string, re.I)

    def _test(obj):
        try:
            val = extract_field_value(obj, attribute_name)
        except NullRelationshipValueEncountered:
            return False
        return val is not None and regex.search(val)

    return _test


FILTER_EXPRESSION_TOKENS = {
    "exact": test_exact,
    "iexact": test_iexact,
    "contains": test_contains,
    "icontains": test_icontains,
    "lt": test_lt,
    "lte": test_lte,
    "gt": test_gt,
    "gte": test_gte,
    "in": test_in,
    "startswith": test_startswith,
    "istartswith": test_istartswith,
    "endswith": test_endswith,
    "iendswith": test_iendswith,
    "range": test_range,
    "isnull": test_isnull,
    "regex": test_regex,
    "iregex": test_iregex,
}


FAKE_QUERYSET_SAFE_METHOD_ATTR = "_modelcluster_fake_queryset_safe_method"
FAKE_QUERYSET_SAFE_METHOD_NAME_ATTR = "_modelcluster_fake_queryset_safe_name"
# Preferred aliases for the decorator metadata attributes.
FAKEQUERYSET_COMPATIBLE_METHOD_ATTR = FAKE_QUERYSET_SAFE_METHOD_ATTR
FAKEQUERYSET_COMPATIBLE_METHOD_NAME_ATTR = FAKE_QUERYSET_SAFE_METHOD_NAME_ATTR
_registered_fake_queryset_classes = {}
_generated_fake_queryset_classes = {}
logger = logging.getLogger(__name__)


class QuerySetMethodOrAttributeUnavailableError(AttributeError):
    pass


def fakequeryset_compatible(method=None, *, as_name=None):
    """
    Mark a QuerySet helper method as safe to run against FakeQuerySet instances.
    """

    def _decorator(decorated_method):
        fake_method_name = as_name or decorated_method.__name__
        existing_attr = inspect.getattr_static(FakeQuerySet, fake_method_name, None)
        if callable(existing_attr):
            logger.warning(
                "fakequeryset_compatible registered method name '%s' conflicts with FakeQuerySet.%s. "
                "Overrides are not supported, so the custom method is ignored",
                fake_method_name,
                fake_method_name,
            )
            return decorated_method
        setattr(decorated_method, FAKE_QUERYSET_SAFE_METHOD_ATTR, True)
        setattr(
            decorated_method,
            FAKE_QUERYSET_SAFE_METHOD_NAME_ATTR,
            fake_method_name,
        )
        return decorated_method

    if method is None:
        return _decorator

    return _decorator(method)


# Backwards-compatible alias for older integrations.
fake_queryset_safe = fakequeryset_compatible


def register_fake_queryset(model):
    """
    Register a custom FakeQuerySet subclass for a model.
    """

    def _decorator(fake_queryset_class):
        _registered_fake_queryset_classes[model] = fake_queryset_class
        return fake_queryset_class

    return _decorator


def _get_safe_fake_queryset_methods(queryset_class):
    methods = {}
    for cls in reversed(queryset_class.__mro__):
        for name, method in cls.__dict__.items():
            if getattr(method, FAKE_QUERYSET_SAFE_METHOD_ATTR, False):
                fake_method_name = getattr(
                    method, FAKE_QUERYSET_SAFE_METHOD_NAME_ATTR, name
                )
                methods[fake_method_name] = method
    return methods


def _get_queryset_class_for_model(model):
    manager = model._default_manager
    return getattr(manager, "_queryset_class", manager.get_queryset().__class__)


def get_fake_queryset_class_for_model(model):
    registered_class = _registered_fake_queryset_classes.get(model)
    if registered_class is not None:
        return registered_class

    generated_class = _generated_fake_queryset_classes.get(model)
    if generated_class is not None:
        return generated_class

    queryset_class = _get_queryset_class_for_model(model)
    safe_methods = _get_safe_fake_queryset_methods(queryset_class)
    if not safe_methods:
        return FakeQuerySet

    generated_class = type(
        "Fake%sQuerySet" % model.__name__, (FakeQuerySet,), safe_methods
    )
    _generated_fake_queryset_classes[model] = generated_class
    return generated_class


def get_fake_queryset_for_model(model, results):
    return get_fake_queryset_class_for_model(model)(model, results)


def _build_test_function_from_filter(model, key_clauses, val):
    # Translate a filter kwarg rule (e.g. foo__bar__exact=123) into a function which can
    # take a model instance and return a boolean indicating whether it passes the rule
    try:
        get_model_field(model, "__".join(key_clauses))
    except FieldDoesNotExist:
        # it is safe to assume the last clause indicates the type of test
        field_match_found = False
    else:
        field_match_found = True

    if not field_match_found and key_clauses[-1] in FILTER_EXPRESSION_TOKENS:
        constructor = FILTER_EXPRESSION_TOKENS[key_clauses.pop()]
    else:
        constructor = test_exact
    # recombine the remaining items to be interpretted
    # by get_model_field() and extract_field_value()
    attribute_name = "__".join(key_clauses)
    return constructor(model, attribute_name, val)


class FakeQuerySetIterable:
    def __init__(self, queryset):
        self.queryset = queryset


class ModelIterable(FakeQuerySetIterable):
    def __iter__(self):
        yield from self.queryset.results


class DictIterable(FakeQuerySetIterable):
    def __iter__(self):
        field_names = self.queryset.dict_fields or [
            field.name for field in self.queryset.model._meta.fields
        ]
        for obj in self.queryset.results:
            yield {
                field_name: extract_field_value(
                    obj,
                    field_name,
                    pk_only=True,
                    suppress_fielddoesnotexist=True,
                    suppress_nullrelationshipvalueencountered=True,
                )
                for field_name in field_names
            }


class ValuesListIterable(FakeQuerySetIterable):
    def __iter__(self):
        field_names = self.queryset.tuple_fields or [
            field.name for field in self.queryset.model._meta.fields
        ]
        for obj in self.queryset.results:
            yield tuple(
                [
                    extract_field_value(
                        obj,
                        field_name,
                        pk_only=True,
                        suppress_fielddoesnotexist=True,
                        suppress_nullrelationshipvalueencountered=True,
                    )
                    for field_name in field_names
                ]
            )


class FlatValuesListIterable(FakeQuerySetIterable):
    def __iter__(self):
        field_name = self.queryset.tuple_fields[0]
        for obj in self.queryset.results:
            yield extract_field_value(
                obj,
                field_name,
                pk_only=True,
                suppress_fielddoesnotexist=True,
                suppress_nullrelationshipvalueencountered=True,
            )


class FakeQuerySet(object):
    @classmethod
    def from_instances(cls, instances, model=None):
        results = list(instances)
        if model is None:
            if not results:
                raise ValueError("Cannot infer model from an empty instance list.")
            model = results[0].__class__
        elif any(not isinstance(instance, model) for instance in results):
            raise TypeError("All instances must be of type %s." % model.__name__)

        if cls is FakeQuerySet:
            return get_fake_queryset_for_model(model, results)

        return cls(model, results)

    def __init__(self, model, results):
        self.model = model
        self.results = results
        self.dict_fields = []
        self.tuple_fields = []
        self.iterable_class = ModelIterable

    def all(self):
        return self

    def get_clone(self, results=None):
        new = type(self)(self.model, results if results is not None else self.results)
        new.dict_fields = self.dict_fields
        new.tuple_fields = self.tuple_fields
        new.iterable_class = self.iterable_class
        return new

    def resolve_q_object(self, q_object):
        connector = q_object.connector
        filters = []

        def test(filters):
            def test_inner(obj):
                result = False
                if connector == Q.AND:
                    result = all([test(obj) for test in filters])
                elif connector == Q.OR:
                    result = any([test(obj) for test in filters])
                else:
                    result = sum([test(obj) for test in filters]) == 1
                if q_object.negated:
                    return not result
                return result

            return test_inner

        for child in q_object.children:
            if isinstance(child, Q):
                filters.append(self.resolve_q_object(child))
            else:
                key_clauses, val = child
                filters.append(
                    _build_test_function_from_filter(
                        self.model, key_clauses.split("__"), val
                    )
                )

        return test(filters)

    def _get_filters(self, *args, **kwargs):
        # a list of test functions; objects must pass all tests to be included
        # in the filtered list
        filters = []

        for q_object in args:
            filters.append(self.resolve_q_object(q_object))

        for key, val in kwargs.items():
            filters.append(
                _build_test_function_from_filter(self.model, key.split("__"), val)
            )

        return filters

    def filter(self, *args, **kwargs):
        filters = self._get_filters(*args, **kwargs)

        clone = self.get_clone(
            results=[
                obj for obj in self.results if all([test(obj) for test in filters])
            ]
        )
        return clone

    def exclude(self, *args, **kwargs):
        filters = self._get_filters(*args, **kwargs)

        clone = self.get_clone(
            results=[
                obj for obj in self.results if not all([test(obj) for test in filters])
            ]
        )
        return clone

    def get(self, *args, **kwargs):
        clone = self.filter(*args, **kwargs)
        result_count = clone.count()

        if result_count == 0:
            raise self.model.DoesNotExist(
                "%s matching query does not exist." % self.model._meta.object_name
            )
        elif result_count == 1:
            for result in clone:
                return result
        else:
            raise self.model.MultipleObjectsReturned(
                "get() returned more than one %s -- it returned %s!"
                % (self.model._meta.object_name, result_count)
            )

    def count(self):
        return len(self.results)

    def exists(self):
        return bool(self.results)

    def first(self):
        for result in self:
            return result

    def last(self):
        if self.results:
            clone = self.get_clone(results=reversed(self.results))
            for result in clone:
                return result

    def select_related(self, *args):
        # has no meaningful effect on non-db querysets
        return self

    def prefetch_related(self, *args):
        prefetch_related_objects(self.results, *args)
        return self

    def only(self, *args):
        # has no meaningful effect on non-db querysets
        return self

    def defer(self, *args):
        # has no meaningful effect on non-db querysets
        return self

    def values(self, *fields):
        clone = self.get_clone()
        clone.dict_fields = fields
        # Ensure all 'fields' are available model fields
        for f in fields:
            get_model_field(self.model, f)
        clone.iterable_class = DictIterable
        return clone

    def values_list(self, *fields, flat=None):
        clone = self.get_clone()
        clone.tuple_fields = fields
        # Ensure all 'fields' are available model fields
        for f in fields:
            get_model_field(self.model, f)
        if flat:
            if len(fields) > 1:
                raise TypeError(
                    "'flat' is not valid when values_list is called with more than one field."
                )
            clone.iterable_class = FlatValuesListIterable
        else:
            clone.iterable_class = ValuesListIterable
        return clone

    def order_by(self, *fields):
        clone = self.get_clone(results=self.results[:])
        sort_by_fields(clone.results, fields)
        return clone

    def distinct(self, *fields):
        unique_results = []
        if not fields:
            fields = [
                field.name for field in self.model._meta.fields if not field.primary_key
            ]
        seen_keys = set()
        for result in self.results:
            key = tuple(str(extract_field_value(result, field)) for field in fields)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_results.append(result)
        return self.get_clone(results=unique_results)

    def none(self):
        """
        Return an empty QuerySet.
        """
        return self.get_clone(results=[])

    # a standard QuerySet will store the results in _result_cache on running the query;
    # this is effectively the same as self.results on a FakeQuerySet, and so we'll make
    # _result_cache an alias of self.results for the benefit of Django internals that
    # exploit it
    def _get_result_cache(self):
        return self.results

    def _set_result_cache(self, val):
        self.results = list(val)

    _result_cache = property(_get_result_cache, _set_result_cache)

    def __getitem__(self, k):
        return self.results[k]

    def __iter__(self):
        iterator = self.iterable_class(self)
        yield from iterator

    def __nonzero__(self):
        return bool(self.results)

    def __repr__(self):
        return repr(list(self))

    def __len__(self):
        return len(self.results)

    def __getattr__(self, method_name):
        if method_name.startswith("__") and method_name.endswith("__"):
            raise AttributeError(method_name)

        raise QuerySetMethodOrAttributeUnavailableError(
            "To support features like 'draft preview' without saving changes to "
            "the database, your model data is being represented in-memory by a "
            "%s instance. This class only implements a subset of the Django QuerySet "
            "API, and only has access to explicitly registered custom queryset methods. "
            "If you would like for '%s' to be available in this context, use the "
            "modelcluster.queryset.fakequeryset_compatible decorator to mark the "
            "method on the QuerySet class used by your model's default manager. "
            "Consider using the 'as_name' option if you would prefer to register a "
            "separate implementation for use in this context."
            % (self.__class__.__name__, method_name)
        )

    ordered = True  # results are returned in a consistent order
    totally_ordered = True
