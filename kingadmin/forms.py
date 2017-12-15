#! /usr/bin/env python
# -*- coding:utf-8 -*-

from django.forms import ModelForm
from django import forms


class FormTest(forms.Form):
    name = forms.CharField(max_length=32)
    age = forms.IntegerField()


def __new__(cls, *args, **kwargs):
    for field_name in cls.base_fields:
        field = cls.base_fields[field_name]
        attr_dic = {"placeholder": field.help_text}
        if "BooleanField" not in field.__repr__():
            attr_dic.update({"class": "form-control"})
            if "ModelChoiceField" in field.__repr__():
                attr_dic.update({"data-tag": field_name})

            if "DateTimeField" in field.__repr__():
                from django.forms.fields import SplitDateTimeField
                if SplitDateTimeField().fields[0]:
                    attr_dic.update({"class": "vDateField datetime", "type": "text", "size": 10})

            elif "DateField" in field.__repr__():
                attr_dic.update({'class': "vDateField", "size": 10, "type": "text"})
            elif "TimeField" in field.__repr__():
                attr_dic.update({"class": "vTimeField", "size": 10, "type": "text"})
        if cls.Meta.admin.readonly_table:
            attr_dic["disabled"] = True

        if cls.Meta.form_create is False:
            if field_name in cls.Meta.admin.readonly_fields:
                attr_dic["disabled"] = True
        field.widget.attrs.update(attr_dic)

        if hasattr(cls.Meta.model, "clean_%s" % field_name):
            clean_field_func = getattr(cls.Meta.model, "clean_%s" % field_name)
            setattr(cls, "clean_%s" % field_name, clean_field_func)
    else:
        if hasattr(cls.Meta.model, "clean2"):
            clean_func = getattr(cls.Meta.model, "clean")
            setattr(cls, "clean", clean_func)
        else:
            setattr(cls, "clean", default_clean)

    return ModelForm.__new__(cls)


def default_clean(self):
    if self.Meta.admin.readonly_table is True:
        raise forms.ValidationError("this is a readonly table !")
    if self.errors:
        raise forms.ValidationError("Please fix errors before re-submit !")
    if self.instance.id is not None:
        for field in self.Meta.admin.readonly_fields:
            field_obj = self.instance._meta.get_field(field)
            if field_obj.get_internal_type() == "ManyToManyField":
                old_field_val = list(getattr(self.instance, field).values("pk"))
                if self.cleaned_data.get(field):
                    form_val = list(self.cleaned_data.get(field).values("pk"))
                else:
                    form_val = []
            else:
                old_field_val = getattr(self.instance, field)
                form_val = self.cleaned_data.get(field)
            if old_field_val != form_val:
                if self.Meta.partial_update:
                    if field not in self.cleaned_data:
                        continue

                self.add_error(field, "Readonly Field: field should be '{value}', not '{new_value}' ".
                               format(**{'value': old_field_val, 'new_value': form_val}))


def create_form(model, fields, admin_class, form_creata=False, **kwargs):
    class Meta:
        pass
    setattr(Meta, "model", model)
    setattr(Meta, "fields", fields)
    setattr(Meta, "admin_class", admin_class)
    setattr(Meta, "form_creata", form_creata)
    setattr(Meta, "partial_update", kwargs.get("partial_update"))
    attrs = {"Meta": Meta}

    if kwargs.get("custom_status"):
        model_form = admin_class.add_form
        for k, v in Meta.__dict__.items():
            if k not in model_form.Meta.__dict__:
                setattr(model_form.Meta, k, v)

    else:
        name = "DynamicModelForm"
        base_classes = (ModelForm, )
        model_form = type(name, base_classes, attrs)

    setattr(model_form, "__new__",  __new__)
    if kwargs.get("request"):
        setattr(model_form, "_request", kwargs.get("request"))
    return model_form

