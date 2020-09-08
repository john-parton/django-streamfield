import json

from copy import deepcopy
from django.db import models
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.urls import reverse
from .base import StreamList, StreamItem
from .settings import (
    BLOCK_OPTIONS,
    SHOW_ADMIN_HELP_TEXT,
    DELETE_BLOCKS_FROM_DB,
    BASE_ADMIN_URL
)


class StreamWidget(forms.Widget):
    template_name = 'streamfield/streamfield_widget.html'

    class Media:
        css = {
            'all': ('streamfield/css/streamfield_widget.css', )
        }
        js = (
            'streamfield/vendor/lodash.min.js',
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

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        model_list_info = {}

        for model in self.model_list:
            as_list = getattr(model, "as_list", False)
            options = getattr(model, "options", BLOCK_OPTIONS)

            model_doc = model._meta.verbose_name_plural if as_list else model._meta.verbose_name

            content_type = ContentType.objects.get_for_model(model)

            model_list_info[content_type.id] = {
                'verbose_name': str(model_doc),
                'abstract': model._meta.abstract,
                'as_list': as_list,
                'options': options,
                'model_name': model._meta.model_name
            }

        attrs['model_list_info'] = json.dumps(model_list_info)
        # Move these elsewhere, this isn't the right place for them
        attrs['show_admin_help_text'] = SHOW_ADMIN_HELP_TEXT
        attrs['delete_blocks_from_db'] = DELETE_BLOCKS_FROM_DB
        attrs['base_admin_url'] = BASE_ADMIN_URL
        attrs['data-popup_size'] = json.dumps(self.popup_size)  # Just make this popup_size_width and popup_size_height or something

        return attrs

    def prepare_value(self, value):
        if isinstance(value, StreamList):
            value = [
                dict(item) for item in value
            ]

        return super().prepare_value(value)


class StreamField(models.JSONField):
    description = "StreamField"

    def __init__(self, *args, **kwargs):
        self.model_list = kwargs.pop('model_list', None)

        kwargs['blank'] = True
        kwargs['default'] = StreamList

        super().__init__(*args, **kwargs)

    def from_db_value(self, *args, **kwargs):
        value = super().from_db_value(*args, **kwargs)

        if isinstance(value, str):
            value = json.loads(value)

        return StreamList(
            StreamItem(item) for item in value
        )

    # def to_python(self, value):
    #     if isinstance(value, StreamList):
    #         return value
    #
    #     # Not totally sure why this would happen?
    #     if isinstance(value, str):
    #         value = json.loads(value)
    #
    #     return StreamList(
    #         StreamItem(item) for item in value
    #     )


    def formfield(self, **kwargs):
        # This is a fairly standard way to set up some defaults
        # while letting the caller override them.
        defaults = {
            'form_class': StreamForm,
            'model_list': self.model_list
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
