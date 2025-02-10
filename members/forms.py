from django import forms
from .models import ConsumptionRecord, RedemptionRecord

# ================================
# 消費紀錄表單 (新增消費)
# ================================
class ConsumptionRecordForm(forms.ModelForm):
    class Meta:
        model = ConsumptionRecord
        fields = ['amount', 'sold_item']


# ================================
# 積分兌換表單
# ================================
class RedeemPointsForm(forms.ModelForm):
    class Meta:
        model = RedemptionRecord
        fields = ['points_used', 'redeemed_item']


# ================================
# Excel 檔案上傳表單 (超級管理者用)
# ================================
class ExcelUploadForm(forms.Form):
    file = forms.FileField(label="上傳 Excel 檔案", help_text="請選擇 .xlsx 或 .xls 格式的文件")
