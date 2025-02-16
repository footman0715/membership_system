"""
Django settings for membership_system project.
"""

import os
import json
from pathlib import Path
import dj_database_url
import gspread
from google.oauth2.service_account import Credentials

# ==============================================================================
# 1. 專案基本設定
# ==============================================================================

# BASE_DIR 為專案的根目錄
BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY：建議在生產環境中由環境變數提供
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-hl^%6noq3x=e&!%bb(f7p#*5+bbso0ss*pitrz!l!23)9pj')

# DEBUG：預設關閉，除非環境變數設定為 True
DEBUG = os.getenv('DEBUG', 'False') == 'False'

# ALLOWED_HOSTS：從環境變數取得允許存取的主機名稱（以逗號分隔）
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(",")

# ==============================================================================
# 2. 安裝的 Django App
# ==============================================================================

INSTALLED_APPS = [
    # Django 內建應用程式
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 自訂的會員系統 App
    'members',
]

# ==============================================================================
# 3. Middleware 設定
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'membership_system.urls'

# ==============================================================================
# 4. Templates 模板設定
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 請確認此資料夾存在，通常放在專案根目錄下
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'membership_system.wsgi.application'

# ==============================================================================
# 5. 資料庫設定
# ==============================================================================

# 從環境變數取得 DATABASE_URL，若未設定則使用預設值（根據你提供的 URL）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://membership_db_user:Onb3q5F0zO5f2qLPk4i3UwWhzgN1dCLG@dpg-culiu3ogph6c73ddauo0-a.oregon-postgres.render.com/membership_db"
).strip().replace("postgresql://", "postgres://")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
else:
    if DEBUG:
        # 本地開發環境若未設定 DATABASE_URL 則使用 SQLite
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / "db.sqlite3",
            }
        }
        print("⚠️ 本地開發模式下未設定 DATABASE_URL，使用 SQLite 資料庫。")
    else:
        # 生產環境必須設定 DATABASE_URL
        raise ValueError("❌ 環境變數 DATABASE_URL 未設定，請在 Render 後台的 Environment 變數中新增它！")

# ==============================================================================
# 6. 密碼驗證設定
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# 7. 語言與時區設定
# ==============================================================================

LANGUAGE_CODE = 'zh-hant'
TIME_ZONE = 'Asia/Taipei'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ==============================================================================
# 8. 靜態檔案設定
# ==============================================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [ BASE_DIR / "static" ]
STATIC_ROOT = BASE_DIR / "staticfiles"

# 指定靜態檔案所在的資料夾，請確保在專案根目錄下建立「static」資料夾


# 當執行 collectstatic 時，靜態檔案會被收集到此資料夾
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# ==============================================================================
# 9. 預設 Primary Key 設定
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# 10. 登入與郵件設定
# ==============================================================================

LOGIN_URL = '/members/login/'

# 測試時使用 console 郵件後端，生產環境建議採用其他郵件服務
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==============================================================================
# 11. Google Sheets API 設定
# ==============================================================================

# 若要啟用 Google Sheets API，請在 Render 的環境變數中設定 GOOGLE_SHEETS_ENABLED 為 True
GOOGLE_SHEETS_ENABLED = os.getenv('GOOGLE_SHEETS_ENABLED', 'False') == 'True'

if GOOGLE_SHEETS_ENABLED:
    try:
        # 從環境變數中讀取 GOOGLE_CREDENTIALS（必須是合法的 JSON 格式字串）
        SERVICE_ACCOUNT_INFO = os.getenv("GOOGLE_CREDENTIALS")
        if SERVICE_ACCOUNT_INFO:
            # 指定正確的 OAuth scope (這裡只需要存取試算表)
            SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
            # 解析 JSON 並建立憑證物件，這裡加入 scopes 參數
            creds = Credentials.from_service_account_info(json.loads(SERVICE_ACCOUNT_INFO), scopes=SCOPES)
            # 利用 gspread 建立 Google Sheets API client
            client = gspread.authorize(creds)
            # 從環境變數讀取試算表相關設定，若未設定則使用預設值
            SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', "1DsDd1YFcUNX6mtSfoLVDfStSNT9GTGcLIhhRS5eH2Ss")
            SHEET_NAME = os.getenv('SHEET_NAME', "Sheet9")
            # 開啟指定試算表與工作表
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
            print(f"✅ 成功連接到試算表: {sheet.title}")
        else:
            print("⚠️ GOOGLE_CREDENTIALS 環境變數未設置，無法使用 Google Sheets API")
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ 找不到試算表，請檢查 SPREADSHEET_ID 是否正確，以及 API 權限")
    except Exception as e:
        print(f"⚠️ 無法初始化 Google Sheets API: {str(e)}")