import json
import warnings

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
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

        # For old values that were migrated
        if isinstance(value, str):
            value = json.loads(value)

        # For old values that used the old system
        for obj in value:
            if 'id' in obj:
                warnings.warn("Got 'id' key in StreamItem instead of object_id.")
                obj['object_id'] = obj.pop('id')

            if not isinstance(obj['object_id'], list):
                warnings.warn("Got non-list 'object_id' in StreamItem.")
                obj['object_id'] = [obj['object_id']]

            if 'model_name' in obj:
                warnings.warn("Got 'model_name' in StreamItem instead of 'content_type_id'.")
                model_name = obj.pop('model_name').lower()

                if 'content_type_id' not in obj:

                    model = next(
                        filter(
                            (lambda model: model._meta.model_name.lower() == model_name),
                            self.model_list
                        )
                    )

                    obj['content_type_id'] = ContentType.objects.get_for_model(model).id

        return [
            StreamItem(**item) for item in value
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
