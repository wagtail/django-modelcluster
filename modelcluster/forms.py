from __future__ import unicode_literals

from django.utils.six import with_metaclass

from django.forms.models import (
    BaseModelFormSet, modelformset_factory,
    ModelForm, _get_foreign_key, ModelFormMetaclass, ModelFormOptions
)

from django.db.models.fields.related import ForeignObjectRel


from modelcluster.models import get_all_child_relations


class BaseTransientModelFormSet(BaseModelFormSet):
    """ A ModelFormSet that doesn't assume that all its initial data instances exist in the db """
    def _construct_form(self, i, **kwargs):
        if self.is_bound and i < self.initial_form_count():
            pk_name = self.model._meta.pk.name
            pk_key = "%s-%s" % (self.add_prefix(i), pk_name)
            pk_val = self.data[pk_key]
            if pk_val:
                kwargs['instance'] = self.queryset.get(**{pk_name: pk_val})
            else:
                kwargs['instance'] = self.model()
        elif i < self.initial_form_count():
            kwargs['instance'] = self.get_queryset()[i]
        elif self.initial_extra:
            # Set initial values for extra forms
            try:
                kwargs['initial'] = self.initial_extra[i - self.initial_form_count()]
            except IndexError:
                pass

        # bypass BaseModelFormSet's own _construct_form
        return super(BaseModelFormSet, self)._construct_form(i, **kwargs)


def transientmodelformset_factory(model, formset=BaseTransientModelFormSet, **kwargs):
    return modelformset_factory(model, formset=formset, **kwargs)


class BaseChildFormSet(BaseTransientModelFormSet):
    def __init__(self, data=None, files=None, instance=None, queryset=None, **kwargs):
        if instance is None:
            self.instance = self.fk.rel.to()
        else:
            self.instance = instance

        self.rel_name = ForeignObjectRel(self.fk, self.fk.rel.to, related_name=self.fk.rel.related_name).get_accessor_name()

        if queryset is None:
            queryset = getattr(self.instance, self.rel_name).all()

        super(BaseChildFormSet, self).__init__(data, files, queryset=queryset, **kwargs)

    def save(self, commit=True):
        # The base ModelFormSet's save(commit=False) will populate the lists
        # self.changed_objects, self.deleted_objects and self.new_objects;
        # use these to perform the appropriate updates on the relation's manager.
        saved_instances = super(BaseChildFormSet, self).save(commit=False)

        manager = getattr(self.instance, self.rel_name)

        # if model has a sort_order_field defined, assign order indexes to the attribute
        # named in it
        if self.can_order and hasattr(self.model, 'sort_order_field'):
            sort_order_field = getattr(self.model, 'sort_order_field')
            for i, form in enumerate(self.ordered_forms):
                setattr(form.instance, sort_order_field, i)

        # If the manager has existing instances with a blank ID, we have no way of knowing
        # whether these correspond to items in the submitted data. We'll assume that they do,
        # as that's the most common case (i.e. the formset contains the full set of child objects,
        # not just a selection of additions / updates) and so we delete all ID-less objects here
        # on the basis that they will be re-added by the formset saving mechanism.
        no_id_instances = [obj for obj in manager.all() if obj.pk is None]
        if no_id_instances:
            manager.remove(*no_id_instances)

        manager.add(*saved_instances)
        manager.remove(*self.deleted_objects)

        if commit:
            manager.commit()

        return saved_instances


def childformset_factory(
    parent_model, model, form=ModelForm,
    formset=BaseChildFormSet, fk_name=None, fields=None, exclude=None,
    extra=3, can_order=False, can_delete=True, max_num=None, validate_max=False,
    formfield_callback=None, widgets=None, min_num=None, validate_min=False
):

    fk = _get_foreign_key(parent_model, model, fk_name=fk_name)
    # enforce a max_num=1 when the foreign key to the parent model is unique.
    if fk.unique:
        max_num = 1
        validate_max = True

    if exclude is None:
        exclude = []
    exclude += [fk.name]

    kwargs = {
        'form': form,
        'formfield_callback': formfield_callback,
        'formset': formset,
        'extra': extra,
        'can_delete': can_delete,
        # if the model supplies a sort_order_field, enable ordering regardless of
        # the current setting of can_order
        'can_order': (can_order or hasattr(model, 'sort_order_field')),
        'fields': fields,
        'exclude': exclude,
        'max_num': max_num,
        'validate_max': validate_max,
        'widgets': widgets,
        'min_num': min_num,
        'validate_min': validate_min,
    }
    FormSet = transientmodelformset_factory(model, **kwargs)
    FormSet.fk = fk
    return FormSet


class ClusterFormOptions(ModelFormOptions):
    def __init__(self, options=None):
        super(ClusterFormOptions, self).__init__(options=options)
        self.formsets = getattr(options, 'formsets', None)
        self.exclude_formsets = getattr(options, 'exclude_formsets', None)


class ClusterFormMetaclass(ModelFormMetaclass):
    extra_form_count = 3

    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, ClusterForm)]
        except NameError:
            # We are defining ClusterForm itself.
            parents = None

        # grab any formfield_callback that happens to be defined in attrs -
        # so that we can pass it on to child formsets - before ModelFormMetaclass deletes it.
        # BAD METACLASS NO BISCUIT.
        formfield_callback = attrs.get('formfield_callback')

        new_class = super(ClusterFormMetaclass, cls).__new__(cls, name, bases, attrs)
        if not parents:
            return new_class

        # ModelFormMetaclass will have set up new_class._meta as a ModelFormOptions instance;
        # replace that with ClusterFormOptions so that we can access _meta.formsets
        opts = new_class._meta = ClusterFormOptions(getattr(new_class, 'Meta', None))
        if opts.model:
            formsets = {}
            for rel in get_all_child_relations(opts.model):
                # to build a childformset class from this relation, we need to specify:
                # - the base model (opts.model)
                # - the child model (rel.field.model)
                # - the fk_name from the child model to the base (rel.field.name)

                rel_name = rel.get_accessor_name()

                # apply 'formsets' and 'exclude_formsets' rules from meta
                if opts.formsets is not None and rel_name not in opts.formsets:
                    continue
                if opts.exclude_formsets and rel_name in opts.exclude_formsets:
                    continue

                try:
                    widgets = opts.widgets.get(rel_name)
                except AttributeError:  # thrown if opts.widgets is None
                    widgets = None

                kwargs = {
                    'extra': cls.extra_form_count,
                    'formfield_callback': formfield_callback,
                    'fk_name': rel.field.name,
                    'widgets': widgets
                }

                # see if opts.formsets looks like a dict; if so, allow the value
                # to override kwargs
                try:
                    kwargs.update(opts.formsets.get(rel_name))
                except AttributeError:
                    pass

                formset = childformset_factory(opts.model, rel.field.model, **kwargs)
                formsets[rel_name] = formset

            new_class.formsets = formsets

        return new_class


class ClusterForm(with_metaclass(ClusterFormMetaclass, ModelForm)):
    def __init__(self, data=None, files=None, instance=None, prefix=None, **kwargs):
        super(ClusterForm, self).__init__(data, files, instance=instance, prefix=prefix, **kwargs)

        self.formsets = {}
        for rel_name, formset_class in self.__class__.formsets.items():
            if prefix:
                formset_prefix = "%s-%s" % (prefix, rel_name)
            else:
                formset_prefix = rel_name
            self.formsets[rel_name] = formset_class(data, files, instance=instance, prefix=formset_prefix)

    def as_p(self):
        form_as_p = super(ClusterForm, self).as_p()
        return form_as_p + ''.join([formset.as_p() for formset in self.formsets.values()])

    def is_valid(self):
        form_is_valid = super(ClusterForm, self).is_valid()
        formsets_are_valid = all([formset.is_valid() for formset in self.formsets.values()])
        return form_is_valid and formsets_are_valid

    def save(self, commit=True):
        instance = super(ClusterForm, self).save(commit=commit)

        # ensure save_m2m is called even if commit = false. We don't fully support m2m fields yet,
        # but if they perform save_form_data in a way that happens to play well with ClusterableModel
        # (as taggit's manager does), we want that to take effect immediately, not just on db save
        if not commit:
            self.save_m2m()

        for formset in self.formsets.values():
            formset.instance = instance
            formset.save(commit=commit)
        return instance
