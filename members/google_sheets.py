import os
import json
import gspread
from google.oauth2.service_account import Credentials

# 設定 Google API 權限範圍
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# 讀取 GOOGLE_CREDENTIALS 環境變數
try:
    google_credentials = os.getenv("GOOGLE_CREDENTIALS")
    if not google_credentials:
        raise ValueError("❌ GOOGLE_CREDENTIALS 環境變數未設置！")

    creds = Credentials.from_service_account_info(
        json.loads(google_credentials),
        scopes=SCOPES  # 設定 API 權限
    )
    client = gspread.authorize(creds)

    # 設定 Google 試算表 ID 和 工作表名稱
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1DsDd1YFcUNX6mtSfoLVDfStSNT9GTGcLIhhRS5eH2Ss")
    SHEET_NAME = os.getenv("SHEET_NAME", "Sheet9")

except Exception as e:
    print(f"⚠️ Google Sheets API 初始化失敗: {e}")
    client = None  # 確保如果錯誤發生，程式不會崩潰


def fetch_google_sheets_data():
    """ 讀取 Google Sheets 資料並返回列表 """
    if not client:
        print("❌ 無法讀取 Google Sheets，API 連線尚未建立！")
        return []

    try:
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        data = sheet.get_all_records()
        if not data:
            print("⚠️ 試算表沒有資料")
        return data
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ 找不到試算表，請檢查 SPREADSHEET_ID 是否正確，以及 API 權限")
        return []
    except gspread.exceptions.APIError as e:
        print(f"❌ Google Sheets API 錯誤: {e}")
        return []
    except Exception as e:
        print(f"⚠️ 發生未知錯誤: {e}")
        return []
