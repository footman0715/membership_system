# casino/urls.py
from django.urls import path
from .views import slot_game, slot_spin

urlpatterns = [
    path('slot/', slot_game, name='slot_game'),
    path('slot/spin/', slot_spin, name='slot_spin'),
]
