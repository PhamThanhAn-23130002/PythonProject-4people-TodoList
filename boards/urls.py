from django.urls import path
from . import views

urlpatterns = [
    path("create_board/", views.create_board, name="create_board"),
    path("card_detail", views.card_detail, name="card_detail"),
    path("home_page", views.home_page, name="home_page"),
    path("home_page2", views.home_page2, name="home_page2"),
    path("home_page_Table", views.home_page_Table, name="home_page_Table"),
]
