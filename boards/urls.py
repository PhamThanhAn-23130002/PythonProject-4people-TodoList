from django.urls import path
from . import views
from accounts import views as av

urlpatterns = [
    # ============================================
    # 1. CÁC TRANG HIỂN THỊ (PAGES)
    # ============================================
    path("home_page", views.home_page, name="home_page"),
    path("home_page2", views.home_page2, name="home_page2"),
    path("home_page_Table", views.home_page_Table, name="home_page_Table"),
    path("about_me", views.about_me, name="about_me"),
    path("log_out", av.logout_view, name="log_out"),
    path('dismiss-intro/', views.dismiss_intro, name='dismiss_intro'),

    # ============================================
    # 2. QUẢN LÝ BẢNG (BOARD)
    # ============================================
    # Trang hiển thị form tạo bảng
    path("create_board/", views.create_board, name="create_board"),
    # Logic xử lý khi bấm nút "Tạo bảng" (POST)
    path("create_board/submit/", views.create_board_logic, name="create_board_logic"),
    
    # Chi tiết bảng, Xóa bảng, Thêm thành viên vào bảng
    path("board/<int:board_id>/", views.board_detail, name="board_detail"),
    path("board/<int:board_id>/delete/", views.delete_board, name="delete_board"),
    path("board/<int:board_id>/add_member/", views.add_member, name="add_member"),
    path('join/<uuid:token>/', views.join_via_link, name='join_via_link'),

    # ============================================
    # 3. API DANH SÁCH (LIST) - Dùng Fetch/Ajax
    # ============================================
    path('api/list/create/', views.create_list_api, name='create_list_api'),
    path('api/list/<int:list_id>/delete/', views.delete_list_api, name='delete_list_api'),

    # ============================================
    # 4. API THẺ (CARD) - Dùng Fetch/Ajax
    # ============================================
    # Tạo thẻ, Xóa thẻ, Đổi tên thẻ
    path('api/card/create/', views.create_card_api, name='create_card_api'),
    path('api/card/<int:card_id>/delete/', views.delete_card_api, name='delete_card_api'),
    path('api/card/update-title/', views.update_card_title, name='update_card_title'),
    
    # Cập nhật Deadline, Thành viên, Lưu mô tả, lưu trạng thái hoàn thành
    path('api/card/<int:card_id>/deadline/', views.update_card_deadline, name='update_card_deadline'),
    path('api/card/member/', views.manage_card_member, name='manage_card_member'),
    path('api/card/update-description/', views.update_card_description, name='update_card_description'),
    path('api/card/<int:card_id>/toggle-completed/', views.toggle_card_completed_api, name='toggle_card_completed_api'),

    # Các view hiển thị chi tiết thẻ (Legacy/Render HTML)
    path("card_detail", views.card_detail, name="card_detail"),
    path("card/<int:card_id>/", views.card_detail_id, name="card_detail_id"),

    # ============================================
    # 5. API CHECKLIST - Dùng Fetch/Ajax
    # ============================================
    path("api/checklist/create/", views.create_checklist, name="create_checklist"),
    path("api/checklist/item/add/", views.add_checklist_item, name="add_checklist_item"),
    path("api/checklist/item/toggle/", views.toggle_checklist_item, name="toggle_checklist_item"),
    path("api/checklist/delete/", views.delete_checklist, name="delete_checklist"),
]