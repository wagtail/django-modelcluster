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
                    "The lookup '{name}' from {model} cannot be replicated "
                    "by modelcluster, because the '{field_name}' "
                    "relationship from {subject_model} is a many-to-many, "
                    "and traversal is only supported for one-to-one or "
                    "many-to-one relationships."
                    .format(
                        name=name,
                        model=model,
                        field_name=field_name,
                        subject_model=subject_model,
                    )
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


def extract_field_value(obj, key, pk_only=False, suppress_fielddoesnotexist=False):
    """
    Attempts to extract a field value from ``obj`` matching the ``key`` - which,
    can contain double-underscores (`'__'`) to indicate traversal of relationships
    to related objects.

    For keys that specify ``ForeignKey`` or ``OneToOneField`` field values, full
    related objects are returned by default. If only the primary key values are
    required ((.g. when ordering, or using ``values()`` or ``values_list()``)),
    call the function with ``pk_only=True``.

    By default, ``FieldDoesNotExist`` is raised if the key cannot be mapped to
    a model field. Call the function with ``suppress_fielddoesnotexist=True``
    to get ``None`` values instead.
    """
    source = obj
    for attr in key.split(REL_DELIMETER):
        if hasattr(source, attr):
            value = getattr(source, attr)
            source = value
            continue
        elif suppress_fielddoesnotexist:
            return None
        else:
            raise FieldDoesNotExist(
                "'{name}' is not a valid field name for {model}".format(
                    name=attr, model=type(source)
                )
            )
    if pk_only and hasattr(value, 'pk'):
        return value.pk
    return value


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
            value = extract_field_value(item, key, pk_only=True, suppress_fielddoesnotexist=True)
            return (value is not None, value)

        # Sort items
        items.sort(key=get_sort_value, reverse=reverse)
