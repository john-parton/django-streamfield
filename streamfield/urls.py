from django.urls import path

from . import views

app_name = 'streamfield'

urlpatterns = [
    path(
        'render/',
        views.RenderWidgetView.as_view(),
        name='admin-render'
    ),
    path(
        'delete/',
        views.DeleteAnyView.as_view(),
        name='delete'
    )
]
