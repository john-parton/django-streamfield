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
    # object_id: typing.Union[int, List[int]]
    # options: Dict

    def get_content_type(self):
        # This is internally cached
        # TODO Return None on abstract model
        return ContentType.objects.get_for_id(self['content_type_id'])

    @cached_property
    def model_class(self):
        return ContentType.objects.get_for_id(self['content_type_id']).model_class()

    @property
    def instance(self):
        if hasattr(self, '_instance'):
            return self._instance

        # TODO Handle abstract model by returning None
        if isinstance(self['object_id'], list):
            if len(self['object_id']) != 1:
                warnings.warn("Attempted to get instance from StreamItem with more than one object_id")
            # Probably won't KeyError
            object_id = self['object_id'][0]
        else:
            object_id = self['object_id']

        self._instance = self.get_content_type().get_object_for_this_type(pk=object_id)
        return self._instance

    @instance.setter
    def instance(self, instance):
        del self._instances
        self._instance = instance

        content_type = ContentType.objects.get_for_model(type(instance))

        self['content_type_id'] = content_type.id
        self['object_id'] = instance.pk

    @instance.deleter
    def instance(self):
        del self._instance

    @property
    def instances(self):
        if hasattr(self, '_instances'):
            return self._instances

        # TODO Handle abstract model by returning []
        if not isisntance(self['object_id'], list):
            warnings.warn("Attempted to get instances from StreamItem with only one object_id")
            ids = [self['object_id']]
        else:
            ids = self['object_id']

        self._instances = list(
            self.model_class()._base_manager.using(self._state.db).filter(
                pk__in=ids
            )
        )

        self._instances.sort(lambda instance: ids.index(instance.pk))

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

    @instances.deleter
    def instances(self):
        del self._instances


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


    def _iterate_over_models(self, callback, tmpl_ctx=None):
        # iterate over models and apply callback function
        data = []
        for stream_item in self:

            model_class = stream_item.model_class()
            model_str = model_class.__name__.lower()
            as_list = getattr(model_class, 'as_list', False)

            context = {
                'model': model_str,
                'unique_id': stream_item['unique_id'],
                'content': stream_item.instances if as_list else stream_item.instance,
                'as_list': as_list,
            }

            if extra_context:
                context.update(extra_context)

            data.append(
                callback(model_class, model_str, content, context)

            )

        return data

    def _render(self, tmpl_ctx=None):
        data = self._iterate_over_models(_get_render_data, tmpl_ctx)
        return mark_safe("".join(data))

    @cached_property
    def render(self):
        return self._render()

    def as_list(self):
        return self._iterate_over_models(_get_data_list)

    # only for complex blocks
    def render_admin(self):
        data = self._iterate_over_models(_get_render_admin_data)
        return mark_safe("".join(data))


def _get_block_tmpl(model_class, model_str):
    if hasattr(model_class, 'block_template'):
        return model_class.block_template
    else:
        return 'streamblocks/%s.html' % model_str.lower()


def _get_render_data(model_class, model_str, context):
    block_tmpl = _get_block_tmpl(model_class, model_str)
    try:
        t = loader.get_template(block_tmpl)
    except loader.TemplateDoesNotExist:
        ctx.update(dict(
            block_tmpl=block_tmpl,
            model_str=model_str
            ))
        t = loader.get_template('streamfield/default_block_tmpl.html')
    return t.render(ctx)

# only for complex blocks
def _get_render_admin_data(model_class, model_str, context):
    t = loader.select_template([
        'streamblocks/admin/%s.html' % model_str.lower(),
        'streamfield/admin/change_form_render_template.html'
        ])

    content = context['content']

    objs = content if isinstance(content, list) else [content]
    return format_html_join(
            '\n', "{}",
            (
                (t.render({
                    'form': get_form_class(model_class)(instance=obj)
                    }),
            ) for obj in objs)
        )

def _get_data_list(model_class, model_str, context):
    return {
        'data': context,
        'template': _get_block_tmpl(model_class, model_str)
    }
