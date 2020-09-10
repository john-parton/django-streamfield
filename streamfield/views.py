# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.http import Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, View
from django.views.generic.edit import ModelFormMixin
from django.views.generic.detail import SingleObjectMixin


# TODO Consider checking a more granular permission?
@method_decorator(staff_member_required, name='dispatch')
class RenderWidgetView(ModelFormMixin, DetailView):

    fields = '__all__'

    @property
    def model(self):
        try:
            return ContentType.objects.get_for_id(self.request.GET.get('content_type_id')).model_class()
        except ContentType.DoesNotExist:
            raise Http404

    def get_object(self, *args, **kwargs):
        try:
            return self.model.objects.get(pk=self.request.GET.get('object_id'))
        except ObjectDoesNotExist:
            raise Http404

    def get_template_names(self):
        if hasattr(self.model, 'custom_admin_template'):
            return [
                self.model.custom_admin_template
            ]

        return [
            f'streamblocks/admin/{self.model._meta.model_name}.html',
            'streamfield/admin/change_form_render_template.html'
        ]


@method_decorator(staff_member_required, name='dispatch')
class DeleteAnyView(SingleObjectMixin, View):

    @property
    def model(self):
        # TODO Only allow models that are specifically registered?
        try:
            return ContentType.objects.get_for_id(self.request.GET.get('content_type_id')).model_class()
        except ContentType.DoesNotExist:
            raise Http404

    def get_object(self, *args, **kwargs):
        try:
            return self.model.objects.get(pk=self.request.GET.get('object_id'))
        except ObjectDoesNotExist:
            raise Http404

    def delete(self):
        self.get_object().delete()

        return JsonResponse({
            'success': True
        })
