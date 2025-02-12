"""
Django settings for membership_system project.
"""

import os
import json
from pathlib import Path
import dj_database_url
import gspread
from google.oauth2.service_account import Credentials

# ==============================
# 1️⃣ 專案基本設定
# ==============================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-hl^%6noq3x=e&!%bb(f7p#*5+bbso0ss*pitrz!l!23)9pj')

DEBUG = os.getenv('DEBUG', 'False') == 'True'  # 預設為 False，除非在環境變數設為 True

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(",")

# ==============================
# 2️⃣ 安裝的 Django APP
# ==============================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'members',  # 會員系統 App
]

# ==============================
# 3️⃣ Middleware
# ==============================

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

# ==============================
# 4️⃣ 模板設定 (Templates)
# ==============================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
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

# ==============================
# 5️⃣ 資料庫設定 (Database) - 使用 Render PostgreSQL
# ==============================

DATABASE_URL = os.getenv("DATABASE_URL", "").strip().replace("postgresql://", "postgres://")

if not DATABASE_URL:
    raise ValueError("❌ 環境變數 DATABASE_URL 未設定，請在 Render 後台的 Environment 變數中新增它！")

DATABASES = {
    'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600, ssl_require=True)
}

# ==============================
# 6️⃣ 密碼驗證設定 (Password Validation)
# ==============================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==============================
# 7️⃣ 語言 & 時區設定 (Language & Timezone)
# ==============================

LANGUAGE_CODE = 'zh-hant'

TIME_ZONE = 'Asia/Taipei'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# ==============================
# 8️⃣ 靜態檔案設定 (Static Files)
# ==============================

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),  # 你的靜態檔案目錄
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # 用於 collectstatic

# ==============================
# 9️⃣ 預設 Primary Key (PK)
# ==============================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================
# 🔹 會員登入登出設定
# ==============================

LOGIN_URL = '/members/login/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==============================
# 🔹 Google Sheets API 設定
# ==============================

GOOGLE_SHEETS_ENABLED = os.getenv('GOOGLE_SHEETS_ENABLED', 'False') == 'True'

if GOOGLE_SHEETS_ENABLED:
    try:
        SERVICE_ACCOUNT_INFO = os.getenv("GOOGLE_CREDENTIALS")

        if SERVICE_ACCOUNT_INFO:
            creds = Credentials.from_service_account_info(json.loads(SERVICE_ACCOUNT_INFO))
            client = gspread.authorize(creds)
            SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', "1DsDd1YFcUNX6mtSfoLVDfStSNT9GTGcLIhhRS5eH2Ss")
            SHEET_NAME = os.getenv('SHEET_NAME', "Sheet9")
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
            print(f"✅ 成功連接到試算表: {sheet.title}")
        else:
            print("⚠️ GOOGLE_CREDENTIALS 環境變數未設置，無法使用 Google Sheets API")
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ 找不到試算表，請檢查 SPREADSHEET_ID 是否正確，以及 API 權限")
    except Exception as e:
        print(f"⚠️ 無法初始化 Google Sheets API: {str(e)}")
