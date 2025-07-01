from django.urls import path
from .views import (
    EnquiryListCreateView,
    ActiveEnquiryListView,
    ClosedEnquiryListView,
    EnquiryDetailView,
    EnquirySummaryByTelecaller,
    EnquiryStatisticsView,
    MettadListCreateView,
    MettadDetailView,
)

urlpatterns = [
    # Enquiry URLs
    path('enquiries/', EnquiryListCreateView.as_view(), name='enquiry-list-create'),
    path('enquiries/active/', ActiveEnquiryListView.as_view(), name='active-enquiry-list'),
    path('enquiries/closed/', ClosedEnquiryListView.as_view(), name='closed-enquiry-list'),
    path('enquiries/<int:pk>/', EnquiryDetailView.as_view(), name='enquiry-detail'),
    path('enquiries/summary/', EnquirySummaryByTelecaller.as_view(), name='enquiry-summary'),
    path('enquiries/statistics/', EnquiryStatisticsView.as_view(), name='enquiry-statistics'),
    
    # Mettad URLs
    path('mettads/', MettadListCreateView.as_view(), name='mettad-list-create'),
    path('mettads/<int:pk>/', MettadDetailView.as_view(), name='mettad-detail'),
]