from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('members/', include('members.urls')  # 將 members App 的 URL 路由引入
    path('casino/', include('casino.urls')),  # 將 casino App 的 URL 路由引入 
]
