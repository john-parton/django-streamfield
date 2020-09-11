from django.template.response import TemplateResponse


# User must inherit this mixin and define own admin
class StreamBlocksAdminMixin:
    change_form_template = 'streamfield/admin/change_form.html'
    popup_response_template = 'streamfield/admin/streamfield_popup_response.html'

    def _popup_response(self, request, action, obj_id):
        return TemplateResponse(request, self.popup_response_template, {
            'action': action,
            'object_id': obj_id
        })

    def response_add(self, request, obj, post_url_continue=None):
        if "block_id" in request.POST:
            return self._popup_response(request, 'add', obj.pk)

        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if "block_id" in request.POST:
            return self._popup_response(request, 'change', obj.pk)

        return super().response_change(request, obj)

    def response_delete(self, request, obj_display, obj_id):
        if "block_id" in request.POST:
            return self._popup_response(request, 'delete', obj_id)

        return super().response_delete(request, obj_display, obj_id)
