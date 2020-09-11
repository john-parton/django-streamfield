from django import forms
from django.conf import settings


class StreamWidget(forms.Widget):
    template_name = 'streamfield/streamfield_widget.html'

    class Media:
        css = {
            'all': ('streamfield/css/streamfield_widget.css', )
        }
        js = (
            'streamfield/vendor/js.cookie.js',
            (
                'streamfield/vendor/vue.js' if settings.DEBUG else 'streamfield/vendor/vue.min.js'
            ),
            'streamfield/vendor/Sortable.min.js',
            'streamfield/vendor/vuedraggable.umd.min.js',
            'streamfield/vendor/axios.min.js',
            'streamfield/js/streamfield_widget.js',
        )
