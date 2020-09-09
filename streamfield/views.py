# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.forms import modelform_factory
from django.http import JsonResponse
from django.http import Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.views.generic.edit import ModelFormMixin


# TODO Consider checking a more granular permission?
@method_decorator(staff_member_required, name='dispatch')
class RenderWidgetView(ModelFormMixin, DetailView):

    @property
    def form_class(self):
        return modelform_factory(self.object.__class__, fields='__all__')

    def get_object(self, *args, **kwargs):
        try:
            content_type = ContentType.objects.get_for_id(self.request.GET.get('content_type_id'))
        except ContentType.DoesNotExist:
            raise Http404

        try:
            return content_type.get_object_for_this_type(pk=self.request.GET.get('object_id'))
        except ObjectDoesNotExist:
            raise Http404

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


@staff_member_required
def delete_instance(request, model_name, pk):
    raise Exception("Test this better")
    t = ContentType.objects.get(app_label='streamblocks', model=model_name)
    obj = t.get_object_for_this_type(pk=pk)
    if request.method == 'DELETE':
        obj.delete()
        resp = {'success': True}
    else:
        resp = {'success': False}
    return JsonResponse(resp)
