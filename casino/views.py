import random
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone

# 你在 members/models.py 裡定義的紀錄表
from members.models import ConsumptionRecord, RedemptionRecord, SlotMachineRecord

@login_required
def slot_game(request):
    """
    顯示「拉霸機遊戲」頁面：
    - 需要使用者已登入 (使用 @login_required)
    - 進入時，就先把目前可用積分算好，傳給模板
    """
    points = get_user_current_points(request.user)
    return render(request, 'casino/slot_game.html', {
        "user_id": request.user.id,    # 用於前端呼叫 API
        "points": points               # 進入頁面時顯示真實剩餘點數
    })


def get_user_current_points(user: User) -> int:
    """
    動態計算使用者「目前可用積分」：
    (消費回饋 + 拉霸贏分) - (兌換花費 + 拉霸下注)
    """
    total_consumption = (
        user.consumption_records.aggregate(total=Sum('reward_points'))['total'] or 0
    )
    total_slot_win = (
        user.slot_records.aggregate(total=Sum('win_points'))['total'] or 0
    )
    total_redemption = (
        user.redemption_records.aggregate(total=Sum('points_used'))['total'] or 0
    )
    total_slot_bet = (
        user.slot_records.aggregate(total=Sum('bet'))['total'] or 0
    )

    current_points = (total_consumption + total_slot_win) - (total_redemption + total_slot_bet)
    return current_points



@csrf_exempt  # 或改用 token/session 保護
def slot_spin(request):
    """
    拉霸機 API (POST):
      1. 接收 user_id, bet
      2. 檢查可用積分是否足夠
      3. 產生結果 + 計算中獎
      4. 寫入 SlotMachineRecord
      5. 回傳 JSON (reels, win_amount, current_points)
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    # 取得前端參數
    user_id = request.POST.get("user_id")
    bet_str = request.POST.get("bet", "10")

    if not user_id:
        return JsonResponse({"error": "Missing user_id."}, status=400)

    # 取得使用者
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

    # 轉成整數 bet
    try:
        bet = int(bet_str)
        if bet <= 0:
            return JsonResponse({"error": "Bet must be a positive integer."}, status=400)
    except ValueError:
        return JsonResponse({"error": "Invalid bet value."}, status=400)

    # 檢查目前積分是否足夠
    current_points = get_user_current_points(user)
    if current_points < bet:
        return JsonResponse({"error": "Not enough points."}, status=400)

    # 產生 3 個符號 (可含 wild)
    possible_symbols = ["symbol1", "symbol2", "symbol3", "symbol4", "wild"]
    reels = [random.choice(possible_symbols) for _ in range(3)]

    # 計算中獎
    win_amount = 0
    if reels[0] == reels[1] == reels[2]:
        if reels[0] == "wild":
            win_amount = bet * 10  # 三個 wild
        else:
            win_amount = bet * 5   # 三個一樣(非 wild)
    else:
        wild_count = reels.count("wild")
        if wild_count == 1:
            win_amount = bet * 2
        elif wild_count == 2:
            win_amount = bet * 3

    # 紀錄本次拉霸結果
    grid_result = " / ".join(reels)
    SlotMachineRecord.objects.create(
        user=user,
        bet=bet,
        grid_result=grid_result,
        win_points=win_amount,
        played_at=timezone.now()
    )

    # 更新後可用積分
    new_points = get_user_current_points(user)

    # 回傳 JSON
    data = {
        "reels": reels,
        "win_amount": win_amount,
        "current_points": new_points
    }
    return JsonResponse(data)