from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
import random

from members.models import ConsumptionRecord, RedemptionRecord, SlotMachineRecord

@login_required
def slot_game(request):
    """
    顯示「拉霸機遊戲頁面」, 需要使用者已登入
    傳入 user_id, points 到模板
    """
    points = get_user_current_points(request.user)
    return render(request, 'casino/slot_game.html', {
        "user_id": request.user.id,
        "points": points
    })


def get_user_current_points(user: User) -> int:
    """
    動態計算使用者目前可用積分
    (消費回饋 + 拉霸贏分) - (兌換 + 拉霸下注)
    """
    total_consumption = (
        user.consumption_records.aggregate(sum=Sum('reward_points'))['sum'] or 0
    )
    total_slot_win = (
        user.slot_records.aggregate(sum=Sum('win_points'))['sum'] or 0
    )
    total_redemption = (
        user.redemption_records.aggregate(sum=Sum('points_used'))['sum'] or 0
    )
    total_slot_bet = (
        user.slot_records.aggregate(sum=Sum('bet'))['sum'] or 0
    )
    return (total_consumption + total_slot_win) - (total_redemption + total_slot_bet)


@csrf_exempt
def slot_spin(request):
    """
    拉霸機後端 API:
      1) 接收 user_id, bet
      2) 檢查積分, 不足則報錯
      3) 為每個捲軸產生「序列」(預設 12 個符號)
         - 最後一個符號當「最終符號」做計算
      4) 計算 win_amount, 寫入 DB
      5) 回傳 reelSequences, win_amount, current_points
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed, use POST."}, status=405)

    user_id = request.POST.get("user_id")
    bet_str = request.POST.get("bet", "10")

    if not user_id:
        return JsonResponse({"error": "Missing user_id."}, status=400)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

    try:
        bet = int(bet_str)
        if bet <= 0:
            return JsonResponse({"error": "Bet must be a positive integer."}, status=400)
    except ValueError:
        return JsonResponse({"error": "Invalid bet value."}, status=400)

    current_points = get_user_current_points(user)
    if current_points < bet:
        return JsonResponse({"error": "Not enough points."}, status=400)

    # 產生 3 條序列, 每條 12 個符號
    possible_symbols = ["symbol1","symbol2","symbol3","symbol4","wild"]
    reel_sequences = []
    final_symbols = []

    for i in range(3):
        seq = []
        # 前面 11 個隨機
        for _ in range(11):
            seq.append(random.choice(possible_symbols))
        # 第 12 個符號 => 最終符號, 也決定中獎
        final_sym = random.choice(possible_symbols)
        seq.append(final_sym)
        reel_sequences.append(seq)
        final_symbols.append(final_sym)

    # 計算中獎
    win_amount = 0
    if final_symbols[0] == final_symbols[1] == final_symbols[2]:
        if final_symbols[0] == "wild":
            win_amount = bet * 10
        else:
            win_amount = bet * 5
    else:
        wild_count = final_symbols.count("wild")
        if wild_count == 1:
            win_amount = bet * 2
        elif wild_count == 2:
            win_amount = bet * 3

    # 寫入 DB
    grid_result = " / ".join(final_symbols)
    SlotMachineRecord.objects.create(
        user=user,
        bet=bet,
        grid_result=grid_result,
        win_points=win_amount,
        played_at=timezone.now()
    )

    new_points = get_user_current_points(user)

    data = {
        "reelSequences": reel_sequences,  # 3 條序列
        "win_amount": win_amount,
        "current_points": new_points
    }
    return JsonResponse(data)
