from django.urls import path
from .views import run_backtest 

urlpatterns = [
    path("run/", run_backtest),
]