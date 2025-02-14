# -*- coding: utf-8 -*-
"""
views.py - 各個功能的 View 定義
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from decimal import Decimal
import openpyxl
import re
from datetime import datetime, timedelta
from django.core.paginator import Paginator

from .forms import (
    ConsumptionRecordForm,
    RedeemPointsForm,
    ProfileEditForm,
    ExcelUploadForm
)
from .models import ConsumptionRecord, RedemptionRecord, GoogleSheetsSyncLog
# ★ 你在 google_sheets.py 中已定義 fetch_google_sheets_data, safe_strip, safe_decimal
from .google_sheets import fetch_google_sheets_data, safe_strip, safe_decimal


def parse_sales_time(sales_time_str):
    """
    彈性解析銷售時間字串，支援：
      1. Django parse_datetime() (ISO 格式等)
      2. 多個 strptime 格式 (含 YYYY/MM/DD、YYYY/MM/DD HH:MM、YYYY-MM-DD ...)
      3. 若都失敗則返回 timezone.now()
    """
    dt = parse_datetime(sales_time_str)
    if dt is not None:
        return dt

    possible_formats = [
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d"
    ]

    for fmt in possible_formats:
        try:
            dt_obj = datetime.strptime(sales_time_str, fmt)
            dt_obj_aware = timezone.make_aware(dt_obj, timezone.get_current_timezone())
            return dt_obj_aware
        except ValueError:
            pass

    match = re.match(r'^(\d{4})/(\d{1,2})/(\d{1,2})$', sales_time_str.strip())
    if match:
        y, m, d = match.groups()
        try:
            dt_obj = datetime(int(y), int(m), int(d))
            dt_obj_aware = timezone.make_aware(dt_obj, timezone.get_current_timezone())
            return dt_obj_aware
        except ValueError:
            pass

    return timezone.now()


# -------------------------
# 1. 使用者註冊
# -------------------------
def register_view(request):
    success_message = None
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            success_message = "恭喜註冊成功囉！"
    else:
        form = UserCreationForm()

    return render(request, 'members/register.html', {
        'form': form,
        'success_message': success_message
    })


# -------------------------
# 2. 使用者登入
# -------------------------
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'members/login.html', {'form': form})


# -------------------------
# 3. 使用者登出
# -------------------------
def logout_view(request):
    logout(request)
    return redirect('login')


# -------------------------
# 4. 會員首頁
# -------------------------
@login_required
def home_view(request):
    return render(request, 'members/home.html')


# -------------------------
# 5. 會員資料顯示 (profile_view)
# -------------------------
@login_required
def profile_view(request):
    """
    顯示會員的消費紀錄(搜尋、分頁)、
    顯示累積積分、顯示一個月內到期的積分、
    顯示歷史使用紀錄(何時使用積分)。
    移除銷售品項的搜尋，改為日期搜尋 (YYYY-MM-DD)
    """
    search_query = request.GET.get('q', '').strip()
    show_more = request.GET.get('show_more', '0')
    page_number = request.GET.get('page', 1)

    # 取得所有消費紀錄 (依銷售時間排序)
    all_records = request.user.consumption_records.all().order_by('-sales_time')
    # 累積回饋積分
    total_points = all_records.aggregate(total=Sum('reward_points'))['total'] or 0

    # 取得使用紀錄(何時使用積分)
    redemption_records = request.user.redemption_records.all().order_by('-redemption_time')

    # 一個月內到期的積分 (需 models.py 有 expiry_date)
    now = timezone.now()
    soon = now + timedelta(days=30)
    expiring_records = all_records.filter(expiry_date__range=(now, soon))
    points_expiring_soon = expiring_records.aggregate(total=Sum('reward_points'))['total'] or 0

    # 日期搜尋 (YYYY-MM-DD)
    if search_query:
        date_obj = parse_date(search_query)
        if date_obj:
            all_records = all_records.filter(sales_time__date=date_obj)
        else:
            # 若解析失敗 => 回傳空集合
            all_records = all_records.none()

    if show_more == '1':
        # 分頁模式：每頁顯示 20 筆
        paginator = Paginator(all_records, 20)
        page_obj = paginator.get_page(page_number)
        return render(request, 'members/profile.html', {
            'is_paginated': True,
            'page_obj': page_obj,
            'search_query': search_query,
            'total_points': total_points,
            'redemption_records': redemption_records,
            'points_expiring_soon': points_expiring_soon,
        })
    else:
        # 預設只顯示最近 10 筆
        records = all_records[:10]
        return render(request, 'members/profile.html', {
            'is_paginated': False,
            'records': records,
            'search_query': search_query,
            'total_points': total_points,
            'redemption_records': redemption_records,
            'points_expiring_soon': points_expiring_soon,
        })


# -------------------------
# 6. 新增消費紀錄
# -------------------------
@login_required
def add_consumption_record(request):
    if request.method == 'POST':
        form = ConsumptionRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            return redirect('profile')
    else:
        form = ConsumptionRecordForm()
    return render(request, 'members/add_consumption_record.html', {'form': form})


# -------------------------
# 7. 會員資料編輯
# -------------------------
@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'members/profile_edit.html', {'form': form})


# -------------------------
# 8. 超級管理者後台
# -------------------------
@user_passes_test(lambda u: u.is_superuser)
def super_admin_dashboard(request):
    """
    超級管理者後台：匯入每日銷售明細、批次更新超級管理者、顯示使用者列表
    """
    message = ""
    if request.method == 'POST':
        # (A) 批次更新超級管理者
        if request.POST.get('action') == 'update_superusers':
            posted_ids = request.POST.getlist('superusers')
            User.objects.exclude(id=request.user.id).update(is_superuser=False)
            if posted_ids:
                User.objects.filter(id__in=posted_ids).update(is_superuser=True)
            message = "已更新超級管理者設定！"

        # (B) 手動同步 Google Sheets (匯入消費紀錄)
        elif 'sync_google_sheets' in request.POST:
            message = update_from_google_sheets()

    members = User.objects.all().order_by('username')
    return render(request, 'members/super_admin_dashboard.html', {
        'message': message,
        'members': members
    })


# ★ 新增：超級管理者編輯指定使用者
@user_passes_test(lambda u: u.is_superuser)
def super_admin_edit_user(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"已成功更新使用者「{user_obj.username}」的資料！")
            return redirect('super_admin_dashboard')
    else:
        form = ProfileEditForm(instance=user_obj)

    return render(request, 'members/super_admin_edit_user.html', {
        'form': form,
        'user_obj': user_obj
    })


# -------------------------
# 9. 超級管理者登入 / 登出
# -------------------------
def super_admin_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                login(request, user)
                return redirect('super_admin_dashboard')
            else:
                form.add_error(None, "您不是超級管理者，無法登入此頁面。")
    else:
        form = AuthenticationForm()
    return render(request, 'members/super_admin_login.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def super_admin_logout_view(request):
    logout(request)
    return redirect('super_admin_login')


# -------------------------
# 10. 積分兌換
# -------------------------
@login_required
def redeem_points_view(request):
    total_reward_points = request.user.consumption_records.aggregate(total=Sum('reward_points'))['total'] or 0
    total_redeemed = request.user.redemption_records.aggregate(total=Sum('points_used'))['total'] or 0
    available_points = total_reward_points - total_redeemed

    message = ""
    if request.method == 'POST':
        form = RedeemPointsForm(request.POST)
        if form.is_valid():
            points_to_redeem = form.cleaned_data['points']
            if points_to_redeem > available_points:
                form.add_error('points', "您沒有足夠的積分來兌換。")
            else:
                RedemptionRecord.objects.create(user=request.user, points_used=points_to_redeem)
                message = f"成功兌換 {points_to_redeem} 積分！"
                available_points -= points_to_redeem
    else:
        form = RedeemPointsForm()

    return render(request, 'members/redeem_points.html', {
        'form': form,
        'available_points': available_points,
        'message': message
    })


# -------------------------
# 11. 手動同步 Google Sheets (抓消費紀錄)
# -------------------------
@user_passes_test(lambda u: u.is_superuser)
def update_from_google_sheets():
    """
    從 Google Sheets 取得資料並同步到 Django 資料庫 (與 Sheet9 保持一致)。
    如果找不到唯一會員 (0 或多筆) 就跳過該筆 (視為非會員)。
    不需要 request 參數 => 方便 management command 或其他地方呼叫。
    """
    records = fetch_google_sheets_data()
    message = "✅ Google Sheets 同步完成！\n"

    # 刪除舊的消費紀錄
    ConsumptionRecord.objects.all().delete()

    for row in records:
        try:
            email = safe_strip(row.get("會員 Email", ""))
            raw_amount = safe_strip(row.get("消費金額(元)", "0")).replace(",", "")
            amount = safe_decimal(raw_amount)

            sold_item = safe_strip(row.get("銷售品項", "未知品項"))
            sales_time_str = safe_strip(row.get("銷售時間", ""))

            # ★ 用 filter() 取代 get()，若非唯一就跳過
            matching_users = User.objects.filter(email=email)
            count = matching_users.count()
            if count == 1:
                # 找到唯一會員 => 正常建立紀錄
                user = matching_users.first()
                sales_time = parse_sales_time(sales_time_str)

                ConsumptionRecord.objects.create(
                    user=user,
                    amount=amount,
                    sold_item=sold_item,
                    sales_time=sales_time
                )
            else:
                # count == 0 => 找不到會員
                # count > 1 => 多筆會員
                # 直接跳過 => 視為非會員，不建立紀錄
                message += f"⚠️ 非會員或多筆會員 Email: {email}，此筆未新增。\n"

        except Exception as e:
            message += f"⚠️ 發生錯誤: {e}\n"

    return message


# -------------------------
# ★ 新增：將會員資料同步到 Google Sheets
# -------------------------
@user_passes_test(lambda u: u.is_superuser)
def sync_users_to_google_sheets(request):
    """
    將所有會員 (User) 資料同步到 Google Sheets 的某個工作表 (Worksheet)
    """
    import os
    import json
    import gspread
    from google.oauth2.service_account import Credentials

    message = ""
    try:
        SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "你的試算表ID")
        WORKSHEET_NAME = "MemberList"

        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_info = os.getenv("GOOGLE_CREDENTIALS", "")
        creds_dict = json.loads(creds_info)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)

        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

        members = User.objects.all().order_by('username')
        data = [
            ["使用者名稱", "Email", "是否超級管理者", "建立日期"]
        ]
        for m in members:
            data.append([
                m.username,
                m.email,
                "是" if m.is_superuser else "否",
                m.date_joined.strftime("%Y-%m-%d %H:%M:%S")
            ])

        sheet.clear()
        sheet.update("A1", data)

        message = "✅ 已將會員資料同步到 Google Sheets"
    except Exception as e:
        message = f"❌ 同步會員資料失敗：{e}"

    messages.info(request, message)
    return redirect('super_admin_dashboard')
