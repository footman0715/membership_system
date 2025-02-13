from django import forms
from .models import ConsumptionRecord, RedemptionRecord
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

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

# ================================
# 定義會員編輯資料只有姓名、Email
# ================================
class ProfileEditForm(UserChangeForm):
    class Meta:
        model = User
        # 只顯示想要的欄位
        fields = ['username', 'first_name', 'last_name', 'email']

# 這裡不要再放任何 HTML 註解或不符合 Python 語法的符號
# 如果需要中文註解，請使用 Python 的 # 或 """ 多行字串 """
