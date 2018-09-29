from __future__ import unicode_literals

import datetime
import re

from django.db.models import Model, prefetch_related_objects

from modelcluster.utils import sort_by_fields


# Constructor for test functions that determine whether an object passes some boolean condition
def test_exact(model, attribute_name, value):
    if isinstance(value, Model):
        if value.pk is None:
            # comparing against an unsaved model, so objects need to match by reference
            return lambda obj: getattr(obj, attribute_name) is value
        else:
            # comparing against a saved model; objects need to match by type and ID.
            # Additionally, where model inheritance is involved, we need to treat it as a
            # positive match if one is a subclass of the other
            def _test(obj):
                other_value = getattr(obj, attribute_name)
                if not (isinstance(value, other_value.__class__) or isinstance(other_value, value.__class__)):
                    return False
                return value.pk == other_value.pk
            return _test
    else:
        field = model._meta.get_field(attribute_name)
        # convert value to the correct python type for this field
        typed_value = field.to_python(value)
        # just a plain Python value = do a normal equality check
        return lambda obj: getattr(obj, attribute_name) == typed_value


def test_iexact(model, attribute_name, match_value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(match_value)

    if match_value is None:
        return lambda obj: getattr(obj, attribute_name) is None
    else:
        match_value = match_value.upper()

        def _test(obj):
            val = getattr(obj, attribute_name)
            return val is not None and val.upper() == match_value

        return _test


def test_contains(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and match_value in val

    return _test


def test_icontains(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(value).upper()

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and match_value in val.upper()

    return _test


def test_lt(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val < match_value

    return _test


def test_lte(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val <= match_value

    return _test


def test_gt(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val > match_value

    return _test


def test_gte(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val >= match_value

    return _test


def test_in(model, attribute_name, value_list):
    field = model._meta.get_field(attribute_name)
    match_values = set(field.to_python(val) for val in value_list)
    return lambda obj: getattr(obj, attribute_name) in match_values


def test_startswith(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.startswith(match_value)

    return _test


def test_istartswith(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(value).upper()

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.upper().startswith(match_value)

    return _test


def test_endswith(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.endswith(match_value)

    return _test


def test_iendswith(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    match_value = field.to_python(value).upper()

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.upper().endswith(match_value)

    return _test


def test_range(model, attribute_name, range_val):
    field = model._meta.get_field(attribute_name)
    start_val = field.to_python(range_val[0])
    end_val = field.to_python(range_val[1])

    def _test(obj):
        val = getattr(obj, attribute_name)
        return (val is not None and val >= start_val and val <= end_val)

    return _test


def test_date(model, attribute_name, match_value):
    def _test(obj):
        val = getattr(obj, attribute_name)
        if isinstance(val, datetime.datetime):
            return val.date() == match_value
        else:
            return val == match_value

    return _test


def test_year(model, attribute_name, match_value):
    match_value = int(match_value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.year == match_value

    return _test


def test_month(model, attribute_name, match_value):
    match_value = int(match_value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.month == match_value

    return _test


def test_day(model, attribute_name, match_value):
    match_value = int(match_value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.day == match_value

    return _test


def test_week(model, attribute_name, match_value):
    match_value = int(match_value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.isocalendar()[1] == match_value

    return _test


def test_week_day(model, attribute_name, match_value):
    match_value = int(match_value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.isoweekday() % 7 + 1 == match_value

    return _test


def test_quarter(model, attribute_name, match_value):
    match_value = int(match_value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and int((val.month - 1) / 3) + 1 == match_value

    return _test


def test_time(model, attribute_name, match_value):
    def _test(obj):
        val = getattr(obj, attribute_name)
        if isinstance(val, datetime.datetime):
            return val.time() == match_value
        else:
            return val == match_value

    return _test


def test_hour(model, attribute_name, match_value):
    match_value = int(match_value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.hour == match_value

    return _test


def test_minute(model, attribute_name, match_value):
    match_value = int(match_value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.minute == match_value

    return _test


def test_second(model, attribute_name, match_value):
    match_value = int(match_value)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and val.second == match_value

    return _test


def test_isnull(model, attribute_name, sense):
    if sense:
        return lambda obj: getattr(obj, attribute_name) is None
    else:
        return lambda obj: getattr(obj, attribute_name) is not None


def test_regex(model, attribute_name, regex_string):
    regex = re.compile(regex_string)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and regex.search(val)

    return _test


def test_iregex(model, attribute_name, regex_string):
    regex = re.compile(regex_string, re.I)

    def _test(obj):
        val = getattr(obj, attribute_name)
        return val is not None and regex.search(val)

    return _test


FILTER_EXPRESSION_TOKENS = {
    'exact': test_exact,
    'iexact': test_iexact,
    'contains': test_contains,
    'icontains': test_icontains,
    'lt': test_lt,
    'lte': test_lte,
    'gt': test_gt,
    'gte': test_gte,
    'in': test_in,
    'startswith': test_startswith,
    'istartswith': test_istartswith,
    'endswith': test_endswith,
    'iendswith': test_iendswith,
    'range': test_range,
    'date': test_date,
    'year': test_year,
    'month': test_month,
    'day': test_day,
    'week': test_week,
    'week_day': test_week_day,
    'quarter': test_quarter,
    'time': test_time,
    'hour': test_hour,
    'minute': test_minute,
    'second': test_second,
    'isnull': test_isnull,
    'regex': test_regex,
    'iregex': test_iregex,
}


def _build_test_function_from_filter(model, key_clauses, val):
    # Translate a filter kwarg rule (e.g. foo__bar__exact=123) into a function which can
    # take a model instance and return a boolean indicating whether it passes the rule
    if len(key_clauses) == 1:
        # key is a single clause; treat as an exact match test
        return test_exact(model, key_clauses[0], val)
    elif len(key_clauses) == 2 and key_clauses[1] in FILTER_EXPRESSION_TOKENS:
        # second clause indicates the type of test
        constructor = FILTER_EXPRESSION_TOKENS[key_clauses[1]]
        return constructor(model, key_clauses[0], val)
    else:
        raise NotImplementedError("Filter expression not supported: %s" % '__'.join(key_clauses))


class FakeQuerySet(object):
    def __init__(self, model, results):
        self.model = model
        self.results = results

    def all(self):
        return self

    def _get_filters(self, **kwargs):
        # a list of test functions; objects must pass all tests to be included
        # in the filtered list
        filters = []

        for key, val in kwargs.items():
            key_clauses = key.split('__')
            filters.append(
                _build_test_function_from_filter(self.model, key_clauses, val)
            )

        return filters

    def filter(self, **kwargs):
        filters = self._get_filters(**kwargs)

        filtered_results = [
            obj for obj in self.results
            if all([test(obj) for test in filters])
        ]

        return FakeQuerySet(self.model, filtered_results)

    def exclude(self, **kwargs):
        filters = self._get_filters(**kwargs)

        filtered_results = [
            obj for obj in self.results
            if not all([test(obj) for test in filters])
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

    def exists(self):
        return bool(self.results)

    def first(self):
        if self.results:
            return self.results[0]

    def last(self):
        if self.results:
            return self.results[-1]

    def select_related(self, *args):
        # has no meaningful effect on non-db querysets
        return self

    def prefetch_related(self, *args):
        prefetch_related_objects(self.results, *args)
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

    def order_by(self, *fields):
        results = self.results[:]  # make a copy of results
        sort_by_fields(results, fields)
        return FakeQuerySet(self.model, results)

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
        return self.results.__iter__()

    def __nonzero__(self):
        return bool(self.results)

    def __repr__(self):
        return repr(list(self))

    def __len__(self):
        return len(self.results)

    ordered = True  # results are returned in a consistent order
