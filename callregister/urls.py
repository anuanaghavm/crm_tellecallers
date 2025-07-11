from django.urls import path
from .views import (
    CallRegisterListCreateView,
    CallRegisterDetailView,
    TelecallerCallStatsView,
    TelecallerDashboardView,
    FollowUpCallsView,
    WalkInListView,
    CallOutcomeFilterView,TelecallerCallSummaryView,AdminJobsView,NotAnsweredCallsView,TelecallerJobsView,EnquiryCallHistoryView
)

urlpatterns = [
    # Basic CRUD operations
    path('calls/', CallRegisterListCreateView.as_view(), name='call-register-list-create'),
    path('calls/<int:pk>/', CallRegisterDetailView.as_view(), name='call-register-detail'),
    
    # Statistics and Dashboard
    path('calls/stats/', TelecallerCallStatsView.as_view(), name='telecaller-call-stats'),
    path('dashboard/', TelecallerDashboardView.as_view(), name='telecaller-dashboard'),
    path('calls/not-answered/',NotAnsweredCallsView.as_view(), name='not-answered-calls'),
    path('enquiry/<int:enquiry_id>/call-history/', EnquiryCallHistoryView.as_view(), name='enquiry-call-history'),

    # Outcome-based filtering
    path('calls/follow-ups/', FollowUpCallsView.as_view(), name='follow-up-calls'),
    path('calls/walk-in-list/', WalkInListView.as_view(), name='walk-in-list'),
    path('calls/outcome/<str:outcome>/', CallOutcomeFilterView.as_view(), name='call-outcome-filter'),
    path('calls-summary/',TelecallerCallSummaryView.as_view(),name="tellecaller-calls-summary"),
    path('jobs-view/',AdminJobsView.as_view(),name="admin-telecallers-jobs"),
    path('jobs-summary/',TelecallerJobsView.as_view(),name="telecallers-job-view")
]