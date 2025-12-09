from django.urls import path
from . import views

urlpatterns = [
    path("create_board/", views.create_board, name="create_board"),
    
]
