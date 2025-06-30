from django.urls import path
from .views import (
    CallRegisterListCreateView,
    CallRegisterDetailView,
    TelecallerCallStatsView,
    TelecallerDashboardView,
    FollowUpCallsView,
    WalkInListView,
    CallOutcomeFilterView,
)

urlpatterns = [
    # Basic CRUD operations
    path('calls/', CallRegisterListCreateView.as_view(), name='call-register-list-create'),
    path('calls/<int:pk>/', CallRegisterDetailView.as_view(), name='call-register-detail'),
    
    # Statistics and Dashboard
    path('calls/stats/', TelecallerCallStatsView.as_view(), name='telecaller-call-stats'),
    path('dashboard/', TelecallerDashboardView.as_view(), name='telecaller-dashboard'),
    
    # Outcome-based filtering
    path('calls/follow-ups/', FollowUpCallsView.as_view(), name='follow-up-calls'),
    path('calls/walk-in-list/', WalkInListView.as_view(), name='walk-in-list'),
    path('calls/outcome/<str:outcome>/', CallOutcomeFilterView.as_view(), name='call-outcome-filter'),
]