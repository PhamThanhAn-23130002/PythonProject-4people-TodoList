from django.urls import path
from . import views

urlpatterns = [
    path('', views.sign_in, name='root'),
    path('login/', views.sign_in, name='sign_in'),
    path('logout/', views.logout_view, name='logout'),
    path("sign-up/", views.sign_up, name="sign_up"),
    path("reset-pass/", views.reset_pass, name="reset_pass"),
    path("verify_code/", views.verify_code, name="verify_code"),
    path("finish_signup/", views.finish_signup, name="finish_signup"),
    path("create_name_pass/", views.create_name_pass, name="create_name_pass"),
    path("verify_acc/", views.verify_acc, name="verify_acc"),
    path("sitepersonal/",views.SitePerSonal,name="sitepersonal"),
    path("setting/",views.setting,name="setting"),
    path("hoatdong/",views.action,name="action"),
    path("the/",views.card,name="cards"),
    path("boadsPersonal/",views.boardspersonal,name="boards"),
    path("members/",views.members,name="members"),
    path('api/send-otp/', views.send_otp_api, name='send_otp_api'),
]
