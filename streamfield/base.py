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
            "model_name": "NumberInText",
            "id": [1,2,3],
            "options":{"margins":true}
        },
        {
            "unique_id": "vlbh7j",
            "model_name": "RichText",
            "id": 1,
            "options": {"margins":true}
        }
    ]
    """


    def _iterate_over_models(self, callback, extra_context=None):
        # iterate over models and apply callback function
        data = []
        for stream_item in self:

            model_class = stream_item.model_class()

            as_list = getattr(model_class, 'as_list', False)

            context = {
                'unique_id': stream_item['unique_id'],
                'content': stream_item.instances if as_list else stream_item.instances[0],
                'as_list': as_list,
                # 'app_label': model._meta.app_label,
                'model_name': model_class._meta.model_name
            }

            if extra_context:
                context.update(extra_context)

            data.append(
                callback(model_class, context)

            )

        return data

    def render(self, extra_context=None):
        data = self._iterate_over_models(_get_render_data, extra_context=extra_context)
        assert False, data
        return mark_safe("".join(data))

    def as_list(self):
        return self._iterate_over_models(_get_data_list)

    # only for complex blocks
    def render_admin(self):
        data = self._iterate_over_models(_get_render_admin_data)
        return mark_safe("".join(data))


def _get_block_tmpl(model_class):
    return getattr(
        model_class,
        'block_template',
        f'streamblocks/{model_class._meta.model_name}.html'
    )


def _get_render_data(model_class, context):
    block_tmpl = _get_block_tmpl(model_class)
    try:
        t = loader.get_template(block_tmpl)
    except loader.TemplateDoesNotExist:
        context['block_tmpl'] = block_tmpl
        t = loader.get_template('streamfield/default_block_tmpl.html')
    return t.render(context)

# only for complex blocks
def _get_render_admin_data(model_class, context):
    model_name = context['model_name']

    t = loader.select_template([
        f'streamblocks/admin/{model_name}.html',
        'streamfield/admin/change_form_render_template.html'
    ])

    content = context['content']

    objs = content if isinstance(content, list) else [content]
    return format_html_join(
        '\n', "{}",
        (
            (
                t.render({
                    'form': get_form_class(model_class)(instance=obj)
                }),
            ) for obj in objs
        )
    )

def _get_data_list(model_class, context):
    return {
        'data': context,
        'template': _get_block_tmpl(model_class)
    }
