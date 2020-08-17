from operator import attrgetter
from django.core.exceptions import FieldDoesNotExist


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

        # Handle sorting by a ForeignKey field or OneToOneField
        try:
            first_item = items[0]
            field = first_item._meta.get_field(key)
            if field.many_to_one or field.one_to_one:
                sort_by_fields(
                    items,
                    [
                        "-%s__%s" % (key, ordering_field) if ordering_field[0] == '-' else "%s__%s" % (key, ordering_field) 
                        for ordering_field in field.remote_field.model._meta.ordering
                    ],
                )
                continue
        except IndexError:
            pass
        except FieldDoesNotExist:
            pass

        # Handle sorting by fields on relations
        if '__' in key:
            getter = attrgetter(key.replace('__', '.'))
        else:
            getter = attrgetter(key)

        # Sort
        # Use a tuple of (v is not None, v) as the key, to ensure that None sorts before other values,
        # as comparing directly with None breaks on python3
        items.sort(key=lambda x: (getter(x) is not None, getter(x)), reverse=reverse)
