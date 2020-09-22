import collections

from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, Value, When, IntegerField
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
        # This returns a "real" queryset with the ordering specified by the location of the key in the index
        return self.model_class().objects.filter(
            pk__in=self.object_id
        ).order_by(
            Case(
                *[
                    When(pk=pk, then=Value(index)) for index, pk in enumerate(self.object_id)
                ],
                output_field=IntegerField()  # Maybe not idea, PK could be non-integral
            )
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
            'model_name': model_class._meta.model_name,
            'options': self.options
        }

        if context['as_list']:
            context['object_list'] = self.instances
        else:
            # Will raise Exception if object was removed or there is more than one object in object_id
            context['object'] = self.instances.get()

        try:
            template = loader.get_template(self.template_path)
        except loader.TemplateDoesNotExist:
            template = loader.get_template('streamfield/default_block_tmpl.html')
            context['template_path'] = self.template_path

        # Need to unwrap template to get real django template... not sure it's the best pattern here
        return template.template, context
