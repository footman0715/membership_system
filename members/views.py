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
from django.utils.dateparse import parse_datetime
from decimal import Decimal
import openpyxl
import re
from datetime import datetime
from django.core.paginator import Paginator

# 從 forms.py 匯入自訂表單
from .forms import (
    ConsumptionRecordForm,
    RedeemPointsForm,
    ProfileEditForm,
    ExcelUploadForm
)
from .models import ConsumptionRecord, RedemptionRecord, GoogleSheetsSyncLog
from .google_sheets import fetch_google_sheets_data, safe_strip, safe_decimal


# -----------------------------------------
# 日期時間解析函式
# -----------------------------------------
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

    # 若依舊失敗，嘗試手動匹配 YYYY/m/d (無前綴 0)
    match = re.match(r'^(\d{4})/(\d{1,2})/(\d{1,2})$', sales_time_str.strip())
    if match:
        y, m, d = match.groups()
        try:
            dt_obj = datetime(int(y), int(m), int(d))
            dt_obj_aware = timezone.make_aware(dt_obj, timezone.get_current_timezone())
            return dt_obj_aware
        except ValueError:
            pass

    # 全部失敗 => 直接使用當前時間
    return timezone.now()


# -----------------------------------------
# 1. 使用者註冊
# -----------------------------------------
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


# -----------------------------------------
# 2. 使用者登入
# -----------------------------------------
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


# -----------------------------------------
# 3. 使用者登出
# -----------------------------------------
def logout_view(request):
    logout(request)
    return redirect('login')


# -----------------------------------------
# 4. 會員首頁
# -----------------------------------------
@login_required
def home_view(request):
    return render(request, 'members/home.html')


# -----------------------------------------
# 5. 會員資料顯示 (profile_view)
# -----------------------------------------
@login_required
def profile_view(request):
    """
    預設顯示最近 10 筆；若 GET 參數 show_more=1 則分頁顯示。
    同時提供搜尋功能 (q) 依銷售品項篩選。
    """
    search_query = request.GET.get('q', '').strip()
    show_more = request.GET.get('show_more', '0')
    page_number = request.GET.get('page', 1)

    all_records = request.user.consumption_records.all()
    total_points = all_records.aggregate(total=Sum('reward_points'))['total'] or 0

    records = all_records.order_by('-sales_time')
    if search_query:
        records = records.filter(sold_item__icontains=search_query)

    if show_more == '1':
        paginator = Paginator(records, 20)
        page_obj = paginator.get_page(page_number)
        return render(request, 'members/profile.html', {
            'is_paginated': True,
            'page_obj': page_obj,
            'search_query': search_query,
            'total_points': total_points,
        })
    else:
        records = records[:10]
        return render(request, 'members/profile.html', {
            'is_paginated': False,
            'records': records,
            'search_query': search_query,
            'total_points': total_points,
        })


# -----------------------------------------
# 6. 新增消費紀錄
# -----------------------------------------
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


# -----------------------------------------
# 7. 會員資料編輯 (移除 is_staff, is_superuser, is_active)
# -----------------------------------------
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


# -----------------------------------------
# 8. 超級管理者後台 (super_admin_dashboard)
# -----------------------------------------
@user_passes_test(lambda u: u.is_superuser)
def super_admin_dashboard(request):
    """
    超級管理者後台：
      - 匯入每日銷售明細
      - 批次更新超級管理者
      - 顯示所有使用者並可進入自訂的使用者編輯頁面
    """
    message = ""
    if request.method == 'POST':
        # (A) 批次更新超級管理者
        if request.POST.get('action') == 'update_superusers':
            posted_ids = request.POST.getlist('superusers')  # 勾選到的使用者 ID 清單
            # 1) 把除了自己以外的使用者全部 is_superuser=False
            User.objects.exclude(id=request.user.id).update(is_superuser=False)
            # 2) 若自己沒有被勾選，但目前是 superuser，也不會被重置 (因為已排除)
            # 3) 把勾選到的使用者設為 True
            if posted_ids:
                User.objects.filter(id__in=posted_ids).update(is_superuser=True)

            message = "已更新超級管理者設定！"

        # (B) 手動同步 Google Sheets
        elif 'sync_google_sheets' in request.POST:
            message = update_from_google_sheets(request)

    # 撈取所有使用者資料
    members = User.objects.all().order_by('username')
    return render(request, 'members/super_admin_dashboard.html', {
        'message': message,
        'members': members
    })


# -----------------------------------------
# ★ 新增：超級管理者編輯指定使用者
# -----------------------------------------
@user_passes_test(lambda u: u.is_superuser)
def super_admin_edit_user(request, user_id):
    """
    讓超級管理者編輯指定 user_id 的使用者資料 (排除 is_staff, is_superuser, is_active)
    """
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


# -----------------------------------------
# 9. 超級管理者登入
# -----------------------------------------
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


# -----------------------------------------
# 10. 積分兌換
# -----------------------------------------
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


# -----------------------------------------
# 11. 手動同步 Google Sheets
# -----------------------------------------
@user_passes_test(lambda u: u.is_superuser)
def update_from_google_sheets(request):
    """
    從 Google Sheets 取得資料並同步到 Django 資料庫 (與 Sheet9 保持一致)
    """
    records = fetch_google_sheets_data()
    message = "✅ Google Sheets 同步完成！\n"

    # 刪除舊的消費紀錄
    ConsumptionRecord.objects.all().delete()

    for row in records:
        try:
            email = safe_strip(row.get("會員 Email", ""))
            raw_amount = safe_strip(row.get("消費金額(元)", "0"))
            raw_amount = raw_amount.replace(",", "")
            amount = safe_decimal(raw_amount)

            sold_item = safe_strip(row.get("銷售品項", "未知品項"))
            sales_time_str = safe_strip(row.get("銷售時間", ""))

            user = User.objects.get(email=email)
            sales_time = parse_sales_time(sales_time_str)

            ConsumptionRecord.objects.create(
                user=user,
                amount=amount,
                sold_item=sold_item,
                sales_time=sales_time
            )

        except User.DoesNotExist:
            message += f"❌ 找不到會員 Email: {email}，該筆紀錄未新增。\n"
        except Exception as e:
            message += f"⚠️ 發生錯誤: {e}\n"

    return message
