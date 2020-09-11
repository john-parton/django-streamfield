import json

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from .base import StreamItem
from .forms import StreamField as StreamFormField


class StreamField(models.JSONField):
    description = "StreamField"

    def __init__(self, *args, **kwargs):

        self._model_list = kwargs.pop('model_list', ())

        kwargs['blank'] = True  # Why?
        kwargs['default'] = list

        super().__init__(*args, **kwargs)

    def from_db_value(self, *args, **kwargs):
        value = super().from_db_value(*args, **kwargs)

        if isinstance(value, str):
            value = json.loads(value)

        return [
            StreamItem(item) for item in value
        ]

    # Not sure this could be more easily accomplished with a LazyObject
    @cached_property
    def model_list(self):
        model_list = []

        for elem in self._model_list:
            # Duck type models
            if hasattr(elem, '_meta') and hasattr(elem._meta, 'model_name'):
                model_list.append(elem)
            else:
                model_list.append(
                    apps.get_model(elem)
                )

        return model_list

    def formfield(self, **kwargs):
        # This is a fairly standard way to set up some defaults
        # while letting the caller override them.
        defaults = {
            'form_class': StreamFormField,
            'model_list': self.model_list
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
