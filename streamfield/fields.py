import json

from django import forms
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property, SimpleLazyObject

from .base import StreamItem
from .settings import (
    BLOCK_OPTIONS,
    SHOW_ADMIN_HELP_TEXT,
    DELETE_BLOCKS_FROM_DB
)


class StreamWidget(forms.Widget):
    template_name = 'streamfield/streamfield_widget.html'

    class Media:
        css = {
            'all': ('streamfield/css/streamfield_widget.css', )
        }
        js = (
            'streamfield/vendor/js.cookie.js',
            'streamfield/vendor/vue.js',  # TODO Use min
            'streamfield/vendor/Sortable.min.js',
            'streamfield/vendor/vuedraggable.umd.min.js',
            'streamfield/vendor/axios.min.js',
            'streamfield/js/streamfield_widget.js',
        )


class StreamForm(forms.JSONField):  # Make name better, move to "fields" module
    widget = StreamWidget

    def __init__(self, model_list, **kwargs):
        self.model_list = model_list
        self.popup_size = kwargs.pop('popup_size', (1000, 500))
        super().__init__(**kwargs)

    def get_model_metadata(self):
        model_list_info = {}

        for model in self.model_list:
            opts = model._meta

            as_list = getattr(model, "as_list", False)

            content_type = ContentType.objects.get_for_model(model)

            model_list_info[content_type.id] = {
                'verbose_name': str(opts.verbose_name_plural if as_list else opts.verbose_name),
                'as_list': as_list,
                'options': getattr(model, "options", BLOCK_OPTIONS),  # Why is the necessary?,
                'admin_url': reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist')
            }

        return json.dumps(model_list_info)

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
        if isinstance(value, list):
            value = [
                dict(item) for item in value
            ]

        return super().prepare_value(value)


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
            'form_class': StreamForm,
            'model_list': self.model_list
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
