from django.urls import path
from .views import Auth, SendCoin, Info, BuyItem

urlpatterns = [
    path("auth/", Auth.as_view(), name="auth"),
    path('info/', Info.as_view(), name='info'),
    path('sendCoin/', SendCoin.as_view(), name='send_coin'),
    path('buy/<str:item>/', BuyItem.as_view(), name='buy_item'),
]