# members/management/commands/update_sheets.py

from django.core.management.base import BaseCommand
# 只引入邏輯函式
from members.views import update_from_google_sheets_logic

class Command(BaseCommand):
    help = "自動從 Google Sheets 取得資料並更新資料庫 (不需 request)"

    def handle(self, *args, **options):
        # 直接呼叫邏輯函式
        message = update_from_google_sheets_logic()
        self.stdout.write(message)
