# -*- coding: utf-8 -*-
"""
views.py - 各個功能的 View 定義
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from decimal import Decimal
import openpyxl

# 匯入本 App 的模型與表單
from .models import ConsumptionRecord, RedemptionRecord, GoogleSheetsSyncLog
from .forms import ConsumptionRecordForm, RedeemPointsForm

# 匯入 Google Sheets 同步及資料清洗輔助函式
from .google_sheets import fetch_google_sheets_data, safe_strip, safe_decimal


# -----------------------------------------
# 1. 使用者註冊
# -----------------------------------------
def register_view(request):
    """ 使用者註冊 """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "註冊成功！")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'members/register.html', {'form': form})


# -----------------------------------------
# 2. 使用者登入
# -----------------------------------------
def login_view(request):
    """ 使用者登入 """
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
    """ 使用者登出 """
    logout(request)
    return redirect('login')


# -----------------------------------------
# 4. 會員首頁
# -----------------------------------------
@login_required
def home_view(request):
    """ 會員首頁 """
    return render(request, 'members/home.html')


# -----------------------------------------
# 5. 會員資料顯示
# -----------------------------------------
@login_required
def profile_view(request):
    """
    會員資料顯示 - 直接顯示 Google Sheets 同步後的消費紀錄
    以銷售時間排序，並計算累積回饋積分
    """
    records = request.user.consumption_records.all().order_by('-sales_time')
    total_points = records.aggregate(total=Sum('reward_points'))['total'] or 0
    
    return render(request, 'members/profile.html', {
        'records': records,
        'total_points': total_points
    })


# -----------------------------------------
# 6. 新增消費紀錄
# -----------------------------------------
@login_required
def add_consumption_record(request):
    """ 新增消費紀錄 """
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
# 7. 會員資料編輯
# -----------------------------------------
@login_required
def profile_edit_view(request):
    """ 編輯會員資料 """
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserChangeForm(instance=request.user)
    return render(request, 'members/profile_edit.html', {'form': form})


# -----------------------------------------
# 8. 超級管理者後台
# -----------------------------------------
@user_passes_test(lambda u: u.is_superuser)
def super_admin_dashboard(request):
    """ 超級管理者後台 """
    message = ""
    if request.method == 'POST':
        if 'sync_google_sheets' in request.POST:
            message = update_from_google_sheets(request)
    members = User.objects.all().order_by('username')
    return render(request, 'members/super_admin_dashboard.html', {
        'message': message,
        'members': members
    })


# -----------------------------------------
# 9. 超級管理者登入 / 登出
# -----------------------------------------
def super_admin_login_view(request):
    """ 超級管理者登入 """
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
    """ 超級管理者登出 """
    logout(request)
    return redirect('super_admin_login')


# -----------------------------------------
# 10. 積分兌換
# -----------------------------------------
@login_required
def redeem_points_view(request):
    """ 積分兌換 """
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
    
    1. 取得資料並刪除現有的消費紀錄。
    2. 對每筆記錄使用 safe_strip 與 safe_decimal 清洗資料。
    3. 嘗試解析「銷售時間」欄位，依次嘗試使用 parse_datetime、"%Y-%m-%d %H:%M:%S" 與 "%Y-%m-%d %H:%M" 格式，
       若均失敗則使用當前時間。
    4. 建立新的 ConsumptionRecord 紀錄。
    5. 若找不到對應會員或發生其它例外，將錯誤訊息累加至 message 字串。
    """
    records = fetch_google_sheets_data()
    message = "✅ Google Sheets 同步完成！\n"

    # 刪除舊的消費紀錄
    ConsumptionRecord.objects.all().delete()

    for row in records:
        try:
            email = safe_strip(row.get("會員 Email", ""))
            # 將「消費金額(元)」先轉為字串並去除逗號，再轉換為 Decimal
            raw_amount = safe_strip(row.get("消費金額(元)", "0"))
            raw_amount = raw_amount.replace(",", "")
            amount = safe_decimal(raw_amount)
            sold_item = safe_strip(row.get("銷售品項", "未知品項"))
            sales_time_str = safe_strip(row.get("銷售時間", ""))

            # 取得會員對象
            user = User.objects.get(email=email)

            # 嘗試解析銷售時間
            parsed_time = parse_datetime(sales_time_str)
            if parsed_time is None:
                try:
                    # 嘗試格式: 2025-02-24 15:30:00
                    sales_time = timezone.datetime.strptime(sales_time_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        # 嘗試格式: 2025-02-24 15:30
                        sales_time = timezone.datetime.strptime(sales_time_str, "%Y-%m-%d %H:%M")
                    except ValueError:
                        sales_time = timezone.now()
            else:
                sales_time = parsed_time

            # 建立消費紀錄
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
