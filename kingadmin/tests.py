from django.test import TestCase

# Create your tests here.

from django.forms import ModelForm
from django import forms


class FormTest(forms.Form):
    name = forms.CharField(max_length=32)
    age = forms.IntegerField()


def __new__(cls, *args, **kwargs):
    for field_name in cls.base_fields:
        field =cls.base_fields[field_name]
        print(dir(field))
