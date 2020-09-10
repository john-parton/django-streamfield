from django.urls import path

from . import views

urlpatterns = [
    path(
        'render/',
        views.RenderWidgetView.as_view(),
        name='streamview-render'
    ),
    path(
        'delete/',
        views.DeleteAnyView.as_view(),
        name='streamview-delete'
    )
]
