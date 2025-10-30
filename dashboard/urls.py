from django.urls import path
from dashboard.views import DashboardStatsView

urlpatterns = [
    path('', DashboardStatsView.as_view())
]
