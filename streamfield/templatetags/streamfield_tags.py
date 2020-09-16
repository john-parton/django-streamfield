import json
import operator as op

from django import template
from django import forms
from django.forms import modelform_factory
from django.utils.text import (
    get_valid_filename,
    camel_case_to_spaces
)
from django.utils.safestring import mark_safe
from django.template import loader

from streamfield.base import StreamItem

register = template.Library()


@register.simple_tag
def format_field(field):
    widget_name = get_widget_name(field)

    default_widget = field.field.widget.template_name.split('/')[-1]

    t = loader.select_template([
        f'streamblocks/admin/widgets/{default_widget}',
        f'streamfield/admin/widgets/{default_widget}',
        'streamfield/admin/widgets/default.html'
    ])

    # Hax
    if widget_name == 'select':

        # ForeignKey Field
        if hasattr(field.field, '_queryset'):
            for obj in field.field._queryset:
                if obj.pk == field.value():
                    field.obj = obj

        # CharField choices
        if hasattr(field.field, '_choices'):
            for obj in field.field._choices:
                if obj[0] == field.value():
                    field.obj = obj[1]

    return t.render({
        'field': field,
        'is_image': isinstance(field, forms.ImageField),
    })


def get_widget_name(field):
    return get_valid_filename(
        camel_case_to_spaces(field.field.widget.__class__.__name__)
    )


# Not a fan of this here
# Difficult to understand and customize
@register.simple_tag
def render_stream_admin(stream_list):
    # Value is usually serialized when we try to pass it in
    if isinstance(stream_list, str):
        stream_list = [
            StreamItem(**item) for item in json.loads(stream_list)
        ]

    chunks = []

    for stream_item in stream_list:
        model_class = stream_item.model_class()

        template = loader.select_template([
            f'streamblocks/admin/{model_class._meta.model_name}.html',
            'streamfield/admin/change_form_render_template.html'
        ])

        form_class = modelform_factory(model_class, fields='__all__')

        for instance in stream_item.instances:
            chunks.append(
                template.render({
                    'form': form_class(instance=instance)
                })
            )

    return mark_safe("".join(chunks))


@register.simple_tag(takes_context=True)
def render_stream(context, stream_list, admin=False):
    chunks = []

    for tmpl, item_context in map(op.methodcaller('get_template_context'), stream_list):
        with context.push(**item_context):
            chunks.append(
                tmpl.render(context)
            )

    return mark_safe(
        "".join(chunks)
    )
