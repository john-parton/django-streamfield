import operator as op

from django import template
from django.utils.text import (
    get_valid_filename,
    camel_case_to_spaces
)
from django.utils.safestring import mark_safe
from django.template import loader

register = template.Library()


@register.simple_tag
def format_field(field):
    widget_name = get_widget_name(field)

    t = loader.select_template([
        f'streamblocks/admin/fields/{widget_name}.html',
        f'streamfield/admin/fields/{widget_name}.html',
        'streamfield/admin/fields/default.html'
    ])

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
        'field': field
    })

def get_widget_name(field):
    return get_valid_filename(
        camel_case_to_spaces(field.field.widget.__class__.__name__)
    )


@register.simple_tag(takes_context=True)
def render_stream(context, stream_list, admin=False):
    chunks = []

    for template, item_context in map(op.methodcaller('get_template_context'), stream_list):
        with context.push(**item_context):
            chunks.append(
                template.render(context)
            )

    return mark_safe(
        "".join(chunks)
    )
