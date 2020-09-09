# -*- coding: utf-8 -*-
from django.forms import modelform_factory
from django.template import loader
from django.http import JsonResponse
from django.http import Http404
from django.contrib.contenttypes.models import ContentType
from django.views.generic import DetailView, TemplateView
from .forms import get_form_class

from django.views.generic.edit import ModelFormMixin


class RenderWidgetView(ModelFormMixin, DetailView):

    @property
    def form_class(self):
        return modelform_factory(self.object.__class__, fields='__all__')

    def get_object(self, *args, **kwargs):
        try:
            content_type = ContentType.objects.get_for_id(self.request.GET.get('content_type_id'))
        except ContentType.DoesNotExist:
            raise Http404

        return content_type.get_object_for_this_type(pk=self.request.GET.get('object_id'))

    def get_template_names(self):
        model = self.object.__class__

        if hasattr(model, 'custom_admin_template'):
            return [
                model.custom_admin_template
            ]

        return [
            f'streamblocks/admin/{model._meta.model_name}.html',
            'streamfield/admin/change_form_render_template.html'
        ]

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['form'] = self.form_class(instance=self.object)
        return context_data



def abstract_block_class(model, base=TemplateView):

    if hasattr(model, 'custom_admin_template'):
        tmpl_name = model.custom_admin_template
    else:
        tmpl = loader.select_template([
            'streamblocks/admin/%s.html' % model.__name__.lower(),
            'streamfield/admin/abstract_block_template.html'
        ])
        tmpl_name = tmpl.template.name

    return type(
        str(model.__name__ + 'TemplateView'), (base, ), {
            'model': model,
            'template_name': tmpl_name,
        }
    )


def delete_instance(request, model_name, pk):
    t = ContentType.objects.get(app_label='streamblocks', model=model_name)
    obj = t.get_object_for_this_type(pk=pk)
    if request.method == 'DELETE':
        obj.delete()
        resp = {'success': True}
    else:
        resp = {'success': False}
    return JsonResponse(resp)
