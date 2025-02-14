from django.core.management.base import BaseCommand
from django.conf import settings
from members.views import update_from_google_sheets

class Command(BaseCommand):
    help = "自動從 Google Sheets 取得資料並更新資料庫"

    def handle(self, *args, **options):
        # 直接呼叫你在 views.py 定義的函式
        update_from_google_sheets(None)  # request 可傳 None 或 mock
