import itertools as it
import json

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.functional import SimpleLazyObject

from .settings import (
    BLOCK_OPTIONS,
    DELETE_BLOCKS_FROM_DB
)
from .widgets import StreamWidget


def unique(iterable):
    seen = set()
    seen_add = seen.add

    for element in it.filterfalse(seen.__contains__, iterable):
        seen_add(element)
        yield element


class StreamField(forms.JSONField):  # Make name better, move to "fields" module
    widget = StreamWidget

    def __init__(self, model_list, **kwargs):
        self.model_list = list(unique(model_list))
        self.popup_size = kwargs.pop('popup_size', (1200, 800))
        super().__init__(**kwargs)

    def get_model_metadata(self):
        # TODO Fix ordering
        metadata = []

        # Remove dupes. There shouldn't be any, but not guaranteed, I guess?
        for model in self.model_list:
            opts = model._meta

            as_list = getattr(model, "as_list", False)

            content_type = ContentType.objects.get_for_model(model, for_concrete_model=False)

            metadata.append({
                'content_type_id': content_type.id,
                'verbose_name': str(opts.verbose_name_plural if as_list else opts.verbose_name),
                'as_list': as_list,
                'options': getattr(model, "options", BLOCK_OPTIONS),  # Why is the necessary?,
                'admin_url': reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist')
            })

        return json.dumps(metadata)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        attrs.update({
            'data-model-metadata': SimpleLazyObject(self.get_model_metadata),
            'data-delete-blocks-from-db': DELETE_BLOCKS_FROM_DB,
            'data-popup-size': json.dumps(self.popup_size),
        })

        return attrs

    def prepare_value(self, value):
        value = [
            item if isinstance(item, dict) else item._asdict() for item in value
        ]

        return super().prepare_value(value)
