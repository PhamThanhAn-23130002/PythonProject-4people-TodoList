from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('card/<int:card_id>/add-tag/', views.add_tag_to_card, name='add_tag_to_card'),
    path('card/<int:card_id>/tag/<int:tag_id>/remove/', views.remove_tag_from_card, name='remove_tag_from_card'),
]