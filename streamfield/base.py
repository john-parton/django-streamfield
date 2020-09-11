import collections

from django.contrib.contenttypes.models import ContentType
from django.template import loader
from django.utils.functional import cached_property


StreamItemBase = collections.namedtuple(
    'StreamItemBase',
    ('unique_id', 'content_type_id', 'object_id', 'options')
)


class StreamItem(StreamItemBase):
    def model_class(self):
        return ContentType.objects.get_for_id(self.content_type_id).model_class()

    @cached_property
    def instances(self):
        # Should this use _base_manager ?
        # Technically this could use a big Case/When construct
        return sorted(
            self.model_class().objects.filter(
                pk__in=self.object_id
            ),
            key=lambda obj: self.object_id.index(obj.pk)
        )

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
            'unique_id': self.unique_id,
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
