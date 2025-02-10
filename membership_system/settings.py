"""
Django settings for membership_system project.
"""

import os
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials

# ==============================
# 1️⃣ 專案基本設定
# ==============================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-hl^x(+%6noq3x=e&!%bb(f7p#*5+bbso0ss*pitrz!l!23)9pj'

DEBUG = True

ALLOWED_HOSTS = []


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
# 5️⃣ 資料庫設定 (Database)
# ==============================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
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

# 確保 credentials.json 在 Django 根目錄
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "credentials.json")

# 設定 Google Sheets API 權限範圍
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# 讀取 Google Sheets 憑證
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# 設定 Google Sheets ID & 工作表名稱
SPREADSHEET_ID = "1DsDd1YFcUNX6mtSfoLVDfStSNT9GTGcLIhhRS5eH2Ss"  # ✅ 你的試算表 ID
SHEET_NAME = "Sheet9"  # ✅ 你的試算表名稱

# 嘗試連接 Google Sheets
try:
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    print(f"✅ 成功連接到試算表: {sheet.title}")
except gspread.exceptions.SpreadsheetNotFound:
    print("❌ 找不到試算表，請檢查 SPREADSHEET_ID 是否正確，以及 API 權限")

import os

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),  # 你的靜態檔案目錄
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # 用於 collectstatic


