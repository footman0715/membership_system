from django.contrib import admin
from django.urls import path, include
from members import views as member_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 管理後台
    path('admin/', admin.site.urls),
    # 根 URL 指向 home_view
    path('', member_views.home_view, name='home'),
    # members App 的 URL 路由
    path('members/', include('members.urls')),
    # 密碼重設相關 URL
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
