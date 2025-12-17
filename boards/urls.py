from django.urls import path
from . import views

urlpatterns = [
    path("create_board/", views.create_board, name="create_board"),
    path("card_detail", views.card_detail, name="card_detail"),
    path("home_page", views.home_page, name="home_page"),
    path("home_page2", views.home_page2, name="home_page2"),
    path("home_page_Table", views.home_page_Table, name="home_page_Table"),
    path("board/<int:board_id>/", views.board_detail, name="board_detail"),
    path("board/<int:board_id>/add_member/", views.add_member, name="add_member"),
    path("board/<int:board_id>/delete/", views.delete_board, name="delete_board"),
]
