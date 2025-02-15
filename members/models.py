from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

# ================================
# 會員消費紀錄 (ConsumptionRecord)
# ================================
class ConsumptionRecord(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='consumption_records'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="消費金額")
    sold_item = models.CharField(max_length=200, help_text="銷售品項")
    sales_time = models.DateTimeField(default=timezone.now, help_text="銷售時間")
    reward_points = models.IntegerField(default=0, help_text="回饋積分")
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="積分到期時間")

    def __str__(self):
        return f"{self.user.username} - {self.amount} 元 - {self.sold_item} - {self.sales_time:%Y-%m-%d %H:%M} - {self.reward_points} 積分"

    def save(self, *args, **kwargs):
        # 1. 如果尚未設定 expiry_date，預設為 sales_time + 365 天
        if not self.expiry_date:
            if not self.sales_time:
                self.sales_time = timezone.now()
            self.expiry_date = self.sales_time + timedelta(days=365)

        # 2. 若 sold_item 為「3x3 拉霸中獎」，直接把 amount 當作 reward_points
        if self.sold_item == "3x3 拉霸中獎":
            self.reward_points = int(self.amount)  # 直接加回
        else:
            # 一般情況：reward_points = 消費金額的 10%
            self.reward_points = int(self.amount * Decimal('0.1'))

        super().save(*args, **kwargs)


# ================================
# 積分兌換紀錄 (RedemptionRecord)
# ================================
class RedemptionRecord(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='redemption_records'
    )
    points_used = models.IntegerField(help_text="兌換使用的積分")
    redeemed_item = models.CharField(max_length=200, default="未指定", help_text="兌換品項")
    redemption_time = models.DateTimeField(default=timezone.now, help_text="兌換時間")

    def __str__(self):
        return f"{self.user.username} - 兌換 {self.redeemed_item} - 使用 {self.points_used} 積分"


# ================================
# Google Sheets 同步記錄
# ================================
class GoogleSheetsSyncLog(models.Model):
    sync_time = models.DateTimeField(default=timezone.now, help_text="同步時間")
    status = models.CharField(max_length=20, choices=[("成功", "成功"), ("失敗", "失敗")], default="成功")
    message = models.TextField(blank=True, null=True, help_text="同步結果描述")

    def __str__(self):
        return f"{self.sync_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.status}"


# ================================
# 拉霸機紀錄 (SlotMachineRecord)
# ================================
class SlotMachineRecord(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='slot_records'
    )
    bet = models.IntegerField(help_text="下注積分")
    grid_result = models.TextField(help_text="3x3 拉霸結果，如：🍒 🍋 🍒 / 🍋 🍋 🍋 / 🔔 🍒 7")
    win_points = models.IntegerField(default=0, help_text="贏得積分(含0)")
    played_at = models.DateTimeField(default=timezone.now, help_text="遊玩時間")

    def __str__(self):
        return f"{self.user.username} - Bet: {self.bet}, Win: {self.win_points}"
