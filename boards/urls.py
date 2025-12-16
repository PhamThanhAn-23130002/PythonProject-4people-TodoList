from django.urls import path
from . import views

urlpatterns = [
    path("create_board/", views.create_board, name="create_board"),
    path("bangcvcuatoi/",views.create_board,name="bangcvcuatoi"),
    path('home/', views.trang_chu, name='boards_home'),
]
