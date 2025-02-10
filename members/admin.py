from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import GoogleSheetsSyncLog

@admin.register(GoogleSheetsSyncLog)
class GoogleSheetsSyncLogAdmin(admin.ModelAdmin):
    list_display = ("sync_time", "status", "message")
    list_filter = ("status",)
    search_fields = ("message",)
