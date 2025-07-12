from django.urls import path
from .views import TelecallerRemindersView,TelecallerCallSummaryView,TelecallerDashboardView

urlpatterns = [
    path('reminders/', TelecallerRemindersView.as_view(), name='telecaller-reminders'),
    path('dashboard/', TelecallerDashboardView.as_view(), name='telecaller-dashboard'),
    path('calls-summary/',TelecallerCallSummaryView.as_view(),name="tellecaller-calls-summary"),

]