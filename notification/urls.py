from django.urls import path
from .views import TelecallerRemindersView

urlpatterns = [
    path('reminders/', TelecallerRemindersView.as_view(), name='telecaller-reminders'),
]