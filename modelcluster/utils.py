from functools import lru_cache
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ManyToManyField, ManyToManyRel

REL_DELIMETER = "__"


class ManyToManyTraversalError(ValueError):
    pass


class TraversedRelationship:
    __slots__ = ['from_model', 'field']

    def __init__(self, from_model, field):
        self.from_model = from_model
        self.field = field

    @property
    def field_name(self) -> str:
        return self.field.name

    @property
    def to_model(self):
        return self.field.target_model


@lru_cache(maxsize=None)
def get_model_field(model, name):
    """
    Returns a model field matching the supplied ``name``, which can include
    double-underscores (`'__'`) to indicate relationship traversal - in which
    case, the model field will be lookuped up from the related model.

    Multiple traversals for the same field are supported, but at this
    moment in time, only traversal of many-to-one and one-to-one relationships
    is supported.

    Details of any relationships traversed in order to reach the returned
    field are made available as `field.traversals`. The value is a tuple of
    ``TraversedRelationship`` instances.

    Raises ``FieldDoesNotExist`` if the name cannot be mapped to a model field.
    """
    subject_model = model
    traversals = []
    field = None
    for field_name in name.split(REL_DELIMETER):

        if field is not None:
            if isinstance(field, (ManyToManyField, ManyToManyRel)):
                raise ManyToManyTraversalError(
                    "The lookup '%(name)s' from %(model)s cannot be replicated "
                    "by modelcluster, because the '%(field_name)s' "
                    "relationship from %(subject_model)s is a many-to-many, "
                    "and traversal is only supported for one-to-one or "
                    "many-to-one relationships." % {
                        'name': name,
                        'model': model,
                        'field_name': field_name,
                        'subject_model': subject_model,
                    }
                )
            if hasattr(field, "related_model"):
                traversals.append(TraversedRelationship(subject_model, field))
                subject_model = field.related_model
        try:
            field = subject_model._meta.get_field(field_name)
        except FieldDoesNotExist:
            if field_name.endswith("_id"):
                field = subject_model._meta.get_field(field_name[:-3]).target_field
            raise

    field.traversals = tuple(traversals)
    return field


def extract_field_value(obj, key, suppress_fielddoesnotexist=False):
    """
    Attempts to extract a field value from ``obj`` matching the ``key`` - which,
    can contain double-underscores (`'__'`) to indicate traversal of relationships
    to related objects.

    Raises ``FieldDoesNotExist`` if the name cannot be mapped to a model field.
    """
    for attr in key.split(REL_DELIMETER):
        if hasattr(obj, key):
            return getattr(obj, key)
        if REL_DELIMETER in key:
            segments = key.split(REL_DELIMETER)
            new_source = extract_field_value(obj, segments.pop(0))
            return extract_field_value(new_source, REL_DELIMETER.join(segments))
        if suppress_fielddoesnotexist:
            return
        raise FieldDoesNotExist(
            "'%(name)s' is not a valid field name for %(model)s." % {
                'name': key, 'model': type(obj)
            }
        )


def sort_by_fields(items, fields):
    """
    Sort a list of objects on the given fields. The field list works analogously to
    queryset.order_by(*fields): each field is either a property of the object,
    or is prefixed by '-' (e.g. '-name') to indicate reverse ordering.
    """
    # To get the desired behaviour, we need to order by keys in reverse order
    # See: https://docs.python.org/2/howto/sorting.html#sort-stability-and-complex-sorts
    for key in reversed(fields):
        # Check if this key has been reversed
        reverse = False
        if key[0] == '-':
            reverse = True
            key = key[1:]

        def get_sort_value(item):
            # Use a tuple of (v is not None, v) as the key, to ensure that None sorts before other values,
            # as comparing directly with None breaks on python3
            value = extract_field_value(item, key)
            return (value is not None, value)

        # Sort items
        items.sort(key=get_sort_value, reverse=reverse)
