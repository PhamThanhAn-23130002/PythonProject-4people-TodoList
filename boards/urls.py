from django.urls import path
from . import views
from accounts import views as av

urlpatterns = [
    path("create_board/", views.create_board, name="create_board"),
    path("card_detail", views.card_detail, name="card_detail"),
    path("card/<int:card_id>/", views.card_detail_id, name="card_detail_id"),
    path("home_page", views.home_page, name="home_page"),
    path("home_page2", views.home_page2, name="home_page2"),
    path("home_page_Table", views.home_page_Table, name="home_page_Table"),
    path("board/<int:board_id>/", views.board_detail, name="board_detail"),
    path("board/<int:board_id>/add_member/", views.add_member, name="add_member"),
    path("board/<int:board_id>/delete/", views.delete_board, name="delete_board"),
    path("boards/<int:board_id>/save/",views.save_board_db,name="save_board_db"),
    path("log_out", av.logout_view, name="log_out"),
    path("about_me", views.about_me, name="about_me"),
    path('join/<uuid:token>/', views.join_via_link, name='join_via_link'),
    path('dismiss-intro/', views.dismiss_intro, name='dismiss_intro'),
    path("api/checklist/create/", views.create_checklist, name="create_checklist"),
    path("api/checklist/item/add/", views.add_checklist_item, name="add_checklist_item"),
    path("api/checklist/item/toggle/", views.toggle_checklist_item, name="toggle_checklist_item"),
    path("api/checklist/delete/", views.delete_checklist, name="delete_checklist"),
    path('api/card/assign_member/', views.assign_member_to_card, name='assign_member_to_card'),
    path('api/card/member/', views.update_card_member, name='update_card_member'),
]
