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


class StreamField(forms.JSONField):  # Make name better, move to "fields" module
    widget = StreamWidget

    def __init__(self, model_list, **kwargs):
        self.model_list = model_list
        self.popup_size = kwargs.pop('popup_size', (1000, 500))
        super().__init__(**kwargs)

    def get_model_metadata(self):
        metadata = {}

        # Remove dupes. There shouldn't be any, but not guaranteed, I guess?
        for model in frozenset(self.model_list):
            opts = model._meta

            as_list = getattr(model, "as_list", False)

            content_type = ContentType.objects.get_for_model(model)

            metadata[content_type.id] = {
                'content_type_id': content_type.id,
                'verbose_name': str(opts.verbose_name_plural if as_list else opts.verbose_name),
                'as_list': as_list,
                'options': getattr(model, "options", BLOCK_OPTIONS),  # Why is the necessary?,
                'admin_url': reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist')
            }

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
        # Could do map(op.methodcaller('_asdict')) but that's PAINFULLY clunky
        value = [
            item._asdict() for item in value
        ]

        return super().prepare_value(value)
