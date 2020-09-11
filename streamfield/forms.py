import json

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.functional import SimpleLazyObject

from .settings import (
    BLOCK_OPTIONS,
    SHOW_ADMIN_HELP_TEXT,
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
        model_metadata = {}

        for model in self.model_list:
            opts = model._meta

            as_list = getattr(model, "as_list", False)

            content_type = ContentType.objects.get_for_model(model)

            # Will overwrite if model is specified more than once
            # Could skip
            model_metadata[content_type.id] = {
                'verbose_name': str(opts.verbose_name_plural if as_list else opts.verbose_name),
                'as_list': as_list,
                'options': getattr(model, "options", BLOCK_OPTIONS),  # Why is the necessary?,
                'admin_url': reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist')
            }

        return json.dumps(model_metadata)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        attrs['model_metadata'] = SimpleLazyObject(self.get_model_metadata)
        # Move these elsewhere, this isn't the right place for them
        attrs['show_admin_help_text'] = SHOW_ADMIN_HELP_TEXT
        attrs['delete_blocks_from_db'] = DELETE_BLOCKS_FROM_DB
        # Just make this popup_size_width and popup_size_height or something
        attrs['data-popup_size'] = json.dumps(self.popup_size)

        return attrs

    def prepare_value(self, value):
        # Could do map(op.methodcaller('_asdict')) but that's PAINFULLY clunky
        value = [
            item._asdict() for item in value
        ]

        return super().prepare_value(value)
