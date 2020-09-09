import collections
import json

from django.contrib.admin import ModelAdmin, site
from django.contrib.contenttypes.models import ContentType
from django.forms import ModelForm
from django.utils.functional import cached_property
from django.utils.html import format_html_join
from django.template import loader
from django.utils.safestring import mark_safe

from .forms import get_form_class


class StreamItem(collections.UserDict):
    # Always has the following keys
    # unique_id: str
    # content_type_id: int
    # object_id: List[int]   # Always a list, even if there's only one value
    # options: Dict

    def model_class(self):
        return ContentType.objects.get_for_id(self['content_type_id']).model_class()

    @property
    def instances(self):
        if hasattr(self, '_instances'):
            return self._instances

        ids = self['object_id']

        # Should this use _base_manager ?
        self._instances = list(
            self.model_class().objects.filter(
                pk__in=ids
            )
        )

        self._instances.sort(key=lambda instance: ids.index(instance.pk))

        return self._instances

    @instances.setter
    def instances(self, instances):
        del self._instance

        instances = list(instances)

        assert instances

        self._instances = instances

        content_type_id = None
        object_id = []

        for instance in instances:
            content_type = ContentType.objects.get_for_model(type(instance))
            if content_type_id is None:
                content_type_id = content_type.id
            elif content_type_id != content_type.id:
                raise Exception("ContentType.id mismatch")

            object_id.append(
                instance.pk
            )

        self['content_type_id'] = content_type_id
        self['object_id'] = object_id

    @property
    def template_path(self):
        model_class = self.model_class()

        return getattr(
            model_class,
            'block_template',
            f'streamblocks/{model_class._meta.model_name}.html'
        )

    def get_template_context(self):
        model_class = self.model_class()

        context = {
            'model_class': model_class,
            'unique_id': self['unique_id'],
            'as_list': getattr(model_class, 'as_list', False),
            # 'app_label': model._meta.app_label,
            'model_name': model_class._meta.model_name
        }

        if context['as_list']:
            context['object_list'] = self.instances
        else:
            context['object'] = self.instances[0]

        try:
            template = loader.get_template(self.template_path)
        except loader.TemplateDoesNotExist:
            template = loader.get_template('streamfield/default_block_tmpl.html')
            context['template_path'] = self.template_path

        # Need to unwrap template to get real django template... not sure it's the best pattern here
        return template.template, context


class StreamList(collections.UserList):
    """
    The instance contains raw data from db and rendered html

    # Example:
    # streamblocks/models.py

    # one value per model
    class RichText(models.Model):
        text = models.TextField(blank=True, null=True, verbose_name='Текстовое поле')

    # list of values per model
    class NumberInText(models.Model):
        big_number = models.CharField(max_length=32)
        small = models.CharField(max_length=32, null=True, blank=True)
        text = models.TextField(null=True, blank=True)

        as_list = True


    # data in db
    value = [
        {
            "unique_id": "lsupu",
            "content_type_id": 23,
            "object_id": [1, 2, 3],
            "options": {
                "margins": true
            }
        },
        {
            "unique_id": "vlbh7j",
            "content_type_id": 23,
            "object_id": 1,
            "options": {
                "margins":true
            }
        }
    ]
    """
