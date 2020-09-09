from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    path(
        'admin-render/',
        views.RenderWidgetView.as_view(),
        name='admin-render'
    ),
    path(
        'admin-instance/<model_name>/<int:pk>/delete/',
        login_required(views.delete_instance),
        name='admin-instance-delete'
    )
]
