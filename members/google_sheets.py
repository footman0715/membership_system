# google_sheets.py
# -------------
# 用於連線並讀取 Google Sheets 資料的輔助模組

import os
import json
import re
import gspread
from decimal import Decimal, InvalidOperation
from google.oauth2.service_account import Credentials

# 1. 設定 Google API 權限範圍
#    最常用的操作 Google Sheets/Drive 的範圍如下：
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 2. 嘗試從環境變數中讀取憑證並建立 gspread 客戶端
try:
    google_credentials = os.getenv("GOOGLE_CREDENTIALS")
    if not google_credentials:
        raise ValueError("❌ GOOGLE_CREDENTIALS 環境變數未設置，無法進行 Google Sheets API 授權！")

    creds = Credentials.from_service_account_info(
        json.loads(google_credentials),
        scopes=SCOPES
    )
    client = gspread.authorize(creds)

    # 從環境變數讀取試算表 ID 和預設工作表名稱
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1DsDd1YFcUNX6mtSfoLVDfStSNT9GTGcLIhhRS5eH2Ss")
    SHEET_NAME = os.getenv("SHEET_NAME", "Sheet9")

except Exception as e:
    print(f"⚠️ Google Sheets API 初始化失敗: {e}")
    client = None  # 若初始化失敗，client 設為 None

# 3. 定義讀取 Google Sheets 資料的函式
def fetch_google_sheets_data():
    """
    連線到預設的 SPREADSHEET_ID & SHEET_NAME，並返回整個表的資料（list of dict）。
    每一列為一個 dict，key 來自標題列，value 為該儲存格的值。
    """
    if not client:
        print("❌ 無法讀取 Google Sheets，因為 client 尚未建立 (API 初始化失敗)！")
        return []

    try:
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        data = sheet.get_all_records()
        if not data:
            print("⚠️ 試算表沒有資料 (空表)")
        return data
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ 找不到試算表，請檢查 SPREADSHEET_ID 是否正確，以及 Service Account 是否擁有存取權")
        return []
    except gspread.exceptions.APIError as e:
        print(f"❌ Google Sheets API 錯誤: {e}")
        return []
    except Exception as e:
        print(f"⚠️ 發生未知錯誤: {e}")
        return []

# 4. 定義安全資料清洗的輔助函式
def safe_strip(value):
    """
    若 value 不是字串，先轉換為字串，再移除前後空白。
    """
    if not isinstance(value, str):
        value = str(value)
    return value.strip()

def safe_decimal(value, default="0"):
    """
    嘗試將 value 轉換成 Decimal，若失敗則返回預設值。
    1. 若 value 非字串，轉為字串並去除前後空白。
    2. 使用正則只保留數字、小數點與負號。
    3. 若結果為空、或包含多個小數點，則返回 default。
    """
    try:
        # 若不是字串，先轉成字串
        if not isinstance(value, str):
            value = str(value)
        value = value.strip()
        if not value:
            print("safe_decimal: 空值，使用預設值", default)
            return Decimal(default)

        # 只保留數字、小數點與負號
        cleaned = re.sub(r"[^\d\.\-]", "", value)
        if not cleaned:
            print("safe_decimal: 清洗後為空，使用預設值", default)
            return Decimal(default)

        # 檢查是否有多個小數點
        if cleaned.count('.') > 1:
            print(f"⚠️ safe_decimal: '{cleaned}' 含多個小數點，使用預設值 {default}")
            return Decimal(default)

        print(f"safe_decimal: 原始='{value}', 清洗後='{cleaned}'")
        return Decimal(cleaned)

    except (InvalidOperation, Exception) as e:
        print(f"⚠️ safe_decimal: 無法將 '{value}' 轉為 Decimal，使用預設值 {default}: {e}")
        return Decimal(default)

# 5. 定義處理單筆記錄的函式
def process_record(record):
    """
    根據欄位名稱做資料清洗：
    - 若欄位包含 "金額", "價格", "數量" 等字樣，嘗試轉成 Decimal。
    - 其他欄位僅去除多餘空白。
    """
    cleaned_record = {}
    for key, value in record.items():
        if key in ["金額", "價格", "數量"]:
            cleaned_record[key] = safe_decimal(value)
        else:
            cleaned_record[key] = safe_strip(value)
    return cleaned_record

def process_google_sheets_data():
    """
    讀取 Google Sheets 並進行資料清洗，返回 list of dict。
    """
    raw_data = fetch_google_sheets_data()
    return [process_record(row) for row in raw_data]

# 6. 測試用主程式 (僅在直接執行 google_sheets.py 時才跑)
if __name__ == '__main__':
    data = process_google_sheets_data()
    print("處理後的資料：")
    for row in data:
        print(row)
