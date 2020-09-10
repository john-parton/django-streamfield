import json

from django.contrib.admin.options import TO_FIELD_VAR
from django.template.response import TemplateResponse


class StreamBlocksAdminMixin:
    change_form_template = 'streamfield/admin/change_form.html'
    popup_response_template = 'streamfield/admin/streamfield_popup_response.html'

    def response_add(self, request, obj, post_url_continue=None):
        if "block_id" in request.POST:
            opts = obj._meta
            to_field = request.POST.get(TO_FIELD_VAR)
            attr = str(to_field) if to_field else opts.pk.attname
            value = obj.serializable_value(attr)

            popup_response_data = json.dumps({
                'app_id': request.POST.get("app_id"),
                'block_id': request.POST.get("block_id"),
                'instance_id': str(value),  # Why is this a string here? -- probably because it's a string down below
            })

            # Why not use render shortcut? or super() ?
            return TemplateResponse(
                request, self.popup_response_template, {
                    'popup_response_data': popup_response_data,
                }
            )

        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if "block_id" in request.POST:

            # Very boilerplate -- just copy the query params a json back into the template
            popup_response_data = json.dumps({
                'action': 'change',
                'app_id': request.POST.get("app_id"),
                'block_id': request.POST.get("block_id"),
                'instance_id': request.POST.get("instance_id"),
            })

            return TemplateResponse(
                request, self.popup_response_template, {
                    'popup_response_data': popup_response_data,
                })

        return super().response_change(request, obj)

    def response_delete(self, request, obj_display, obj_id):
        if "block_id" in request.POST:
            popup_response_data = json.dumps({
                'action': 'delete',
                'value': str(obj_id),
                'app_id': request.POST.get("app_id"),
                'block_id': request.POST.get("block_id"),
                'instance_id': request.POST.get("instance_id"),
            })

            return TemplateResponse(request, self.popup_response_template, {
                'popup_response_data': popup_response_data,
            })

        return super().response_delete(request, obj_display, obj_id)

# if user defined admin for his blocks, then do not autoregiser block models
