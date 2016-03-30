from __future__ import unicode_literals

import json
import datetime

from django.db import models
from django.db.models.fields.related import ForeignObjectRel
from django.db.models.fields import FieldDoesNotExist
from django.utils.encoding import is_protected_type
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.utils import timezone


def get_field_value(field, model):
    if field.rel is None:
        value = field.pre_save(model, add=model.pk is None)

        # Make datetimes timezone aware
        # https://github.com/django/django/blob/master/django/db/models/fields/__init__.py#L1394-L1403
        if isinstance(value, datetime.datetime) and settings.USE_TZ:
            if timezone.is_naive(value):
                default_timezone = timezone.get_default_timezone()
                value = timezone.make_aware(value, default_timezone).astimezone(timezone.utc)
            # convert to UTC
            value = timezone.localtime(value, timezone.utc)

        if is_protected_type(value):
            return value
        else:
            return field.value_to_string(model)
    else:
        return getattr(model, field.get_attname())


def get_serializable_data_for_fields(model):
    pk_field = model._meta.pk
    # If model is a child via multitable inheritance, use parent's pk
    while pk_field.rel and pk_field.rel.parent_link:
        pk_field = pk_field.rel.to._meta.pk

    obj = {'pk': get_field_value(pk_field, model)}

    for field in model._meta.fields:
        if field.serialize:
            obj[field.name] = get_field_value(field, model)

    return obj


def model_from_serializable_data(model, data, check_fks=True, strict_fks=False):
    pk_field = model._meta.pk
    # If model is a child via multitable inheritance, use parent's pk
    while pk_field.rel and pk_field.rel.parent_link:
        pk_field = pk_field.rel.to._meta.pk

    kwargs = {pk_field.attname: data['pk']}
    for field_name, field_value in data.items():
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            continue

        # Filter out reverse relations
        if isinstance(field, ForeignObjectRel):
            continue

        if field.rel and isinstance(field.rel, models.ManyToManyRel):
            raise Exception('m2m relations not supported yet')
        elif field.rel and isinstance(field.rel, models.ManyToOneRel):
            if field_value is None:
                kwargs[field.attname] = None
            else:
                clean_value = field.rel.to._meta.get_field(field.rel.field_name).to_python(field_value)
                kwargs[field.attname] = clean_value
                if check_fks:
                    try:
                        field.rel.to._default_manager.get(**{field.rel.field_name: clean_value})
                    except field.rel.to.DoesNotExist:
                        if field.rel.on_delete == models.DO_NOTHING:
                            pass
                        elif field.rel.on_delete == models.CASCADE:
                            if strict_fks:
                                return None
                            else:
                                kwargs[field.attname] = None

                        elif field.rel.on_delete == models.SET_NULL:
                            kwargs[field.attname] = None

                        else:
                            raise Exception("can't currently handle on_delete types other than CASCADE, SET_NULL and DO_NOTHING")
        else:
            value = field.to_python(field_value)

            # Make sure datetimes are converted to localtime
            if isinstance(field, models.DateTimeField) and settings.USE_TZ and value is not None:
                default_timezone = timezone.get_default_timezone()
                if timezone.is_aware(value):
                    value = timezone.localtime(value, default_timezone)
                else:
                    value = timezone.make_aware(value, default_timezone)

            kwargs[field.name] = value

    obj = model(**kwargs)

    if data['pk'] is not None:
        # Set state to indicate that this object has come from the database, so that
        # ModelForm validation doesn't try to enforce a uniqueness check on the primary key
        obj._state.adding = False

    return obj


def get_all_child_relations(model):
    """
    Return a list of RelatedObject records for child relations of the given model,
    including ones attached to ancestors of the model
    """
    try:
        return model._meta._child_relations_cache
    except AttributeError:
        relations = []
        for parent in model._meta.get_parent_list():
            try:
                relations.extend(parent._meta.child_relations)
            except AttributeError:
                pass

        try:
            relations.extend(model._meta.child_relations)
        except AttributeError:
            pass

        model._meta._child_relations_cache = relations
        return relations


class ClusterableModel(models.Model):
    def __init__(self, *args, **kwargs):
        """
        Extend the standard model constructor to allow child object lists to be passed in
        via kwargs
        """
        child_relation_names = [rel.get_accessor_name() for rel in get_all_child_relations(self)]

        is_passing_child_relations = False
        for rel_name in child_relation_names:
            if rel_name in kwargs:
                is_passing_child_relations = True
                break

        if is_passing_child_relations:
            kwargs_for_super = kwargs.copy()
            relation_assignments = {}
            for rel_name in child_relation_names:
                if rel_name in kwargs:
                    relation_assignments[rel_name] = kwargs_for_super.pop(rel_name)

            super(ClusterableModel, self).__init__(*args, **kwargs_for_super)
            for (field_name, related_instances) in relation_assignments.items():
                setattr(self, field_name, related_instances)
        else:
            super(ClusterableModel, self).__init__(*args, **kwargs)

    def save(self, **kwargs):
        """
        Save the model and commit all child relations.
        """
        child_relation_names = [rel.get_accessor_name() for rel in get_all_child_relations(self)]

        update_fields = kwargs.pop('update_fields', None)
        if update_fields is None:
            real_update_fields = None
            relations_to_commit = child_relation_names
        else:
            real_update_fields = []
            relations_to_commit = []
            for field in update_fields:
                if field in child_relation_names:
                    relations_to_commit.append(field)
                else:
                    real_update_fields.append(field)

        super(ClusterableModel, self).save(update_fields=real_update_fields, **kwargs)

        for relation in relations_to_commit:
            getattr(self, relation).commit()

    def serializable_data(self):
        obj = get_serializable_data_for_fields(self)
        child_relations = get_all_child_relations(self)

        for rel in child_relations:
            rel_name = rel.get_accessor_name()
            children = getattr(self, rel_name).all()

            if hasattr(rel.related_model, 'serializable_data'):
                obj[rel_name] = [child.serializable_data() for child in children]
            else:
                obj[rel_name] = [get_serializable_data_for_fields(child) for child in children]

        return obj

    def to_json(self):
        return json.dumps(self.serializable_data(), cls=DjangoJSONEncoder)

    @classmethod
    def from_serializable_data(cls, data, check_fks=True, strict_fks=False):
        """
        Build an instance of this model from the JSON-like structure passed in,
        recursing into related objects as required.
        If check_fks is true, it will check whether referenced foreign keys still
        exist in the database.
        - dangling foreign keys on related objects are dealt with by either nullifying the key or
        dropping the related object, according to the 'on_delete' setting.
        - dangling foreign keys on the base object will be nullified, unless strict_fks is true,
        in which case any dangling foreign keys with on_delete=CASCADE will cause None to be
        returned for the entire object.
        """
        obj = model_from_serializable_data(cls, data, check_fks=check_fks, strict_fks=strict_fks)
        if obj is None:
            return None

        child_relations = get_all_child_relations(cls)

        for rel in child_relations:
            rel_name = rel.get_accessor_name()
            try:
                child_data_list = data[rel_name]
            except KeyError:
                continue

            related_model = rel.related_model
            if hasattr(related_model, 'from_serializable_data'):
                children = [
                    related_model.from_serializable_data(child_data, check_fks=check_fks, strict_fks=True)
                    for child_data in child_data_list
                ]
            else:
                children = [
                    model_from_serializable_data(related_model, child_data, check_fks=check_fks, strict_fks=True)
                    for child_data in child_data_list
                ]

            children = filter(lambda child: child is not None, children)

            setattr(obj, rel_name, children)

        return obj

    @classmethod
    def from_json(cls, json_data, check_fks=True, strict_fks=False):
        return cls.from_serializable_data(json.loads(json_data), check_fks=check_fks, strict_fks=strict_fks)

    class Meta:
        abstract = True
