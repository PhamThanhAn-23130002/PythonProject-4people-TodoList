from django.urls import path
from . import views

urlpatterns = [
    path('api/get-notifications/', views.get_notifications_api, name='get_notifications_api'),
    path('api/mark-read/<int:noti_id>/', views.mark_read_api, name='mark_read_api'),
]