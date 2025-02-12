import os
import json
import gspread
from decimal import Decimal, InvalidOperation
from google.oauth2.service_account import Credentials

# -----------------------------
# 1. 設定 Google API 權限範圍
# -----------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# -----------------------------
# 2. 讀取 GOOGLE_CREDENTIALS 環境變數並建立連線
# -----------------------------
try:
    google_credentials = os.getenv("GOOGLE_CREDENTIALS")
    if not google_credentials:
        raise ValueError("❌ GOOGLE_CREDENTIALS 環境變數未設置！")

    creds = Credentials.from_service_account_info(
        json.loads(google_credentials),
        scopes=SCOPES
    )
    client = gspread.authorize(creds)

    # 設定 Google 試算表 ID 和 工作表名稱
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1DsDd1YFcUNX6mtSfoLVDfStSNT9GTGcLIhhRS5eH2Ss")
    SHEET_NAME = os.getenv("SHEET_NAME", "Sheet9")
except Exception as e:
    print(f"⚠️ Google Sheets API 初始化失敗: {e}")
    client = None  # 若初始化失敗，client 設為 None

# -----------------------------
# 3. 定義資料讀取與錯誤處理函式
# -----------------------------
def fetch_google_sheets_data():
    """
    讀取 Google Sheets 資料並返回列表
    """
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

# -----------------------------
# 4. 定義安全資料清洗輔助函式
# -----------------------------
def safe_strip(value):
    """
    若 value 不是字串，先轉換為字串，再移除前後空白
    """
    if not isinstance(value, str):
        value = str(value)
    return value.strip()

def safe_decimal(value, default="0"):
    """
    嘗試將 value 轉換成 Decimal，若失敗則返回預設值
    """
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    try:
        return Decimal(value)
    except InvalidOperation:
        print(f"⚠️ 無法將 '{value}' 轉換為 Decimal，使用預設值 {default}")
        return Decimal(default)

# -----------------------------
# 5. 定義處理單筆記錄的函式
# -----------------------------
def process_record(record):
    """
    根據欄位名稱處理單筆記錄的資料清洗
    假設 "金額"、"價格"、"數量" 等欄位預期為數字，其它欄位則清除多餘空白
    """
    cleaned_record = {}
    for key, value in record.items():
        # 若欄位名稱預期為數字，則嘗試轉換為 Decimal
        if key in ["金額", "價格", "數量"]:
            cleaned_record[key] = safe_decimal(value)
        else:
            cleaned_record[key] = safe_strip(value)
    return cleaned_record

def process_google_sheets_data():
    """
    取得並處理 Google Sheets 的所有資料，返回清洗後的資料列表
    """
    raw_data = fetch_google_sheets_data()
    return [process_record(record) for record in raw_data]

# -----------------------------
# 6. 測試用主程式
# -----------------------------
if __name__ == '__main__':
    data = process_google_sheets_data()
    print("處理後的資料：")
    for row in data:
        print(row)
