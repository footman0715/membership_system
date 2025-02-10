from django.urls import path
from . import views

urlpatterns = [
    # 會員功能
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/add_record/', views.add_consumption_record, name='add_record'),

    # 超級管理者功能
    path('super_admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super_admin/login/', views.super_admin_login_view, name='super_admin_login'),
    path('super_admin/logout/', views.super_admin_logout_view, name='super_admin_logout'),
    path('super_admin/sync_google_sheets/', views.update_from_google_sheets, name='sync_google_sheets'),

    # 積分相關功能
    path('redeem_points/', views.redeem_points_view, name='redeem_points'),
]
