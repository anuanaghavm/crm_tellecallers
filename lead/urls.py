from django.urls import path
from .views import (
    EnquiryListCreateView,
    EnquiryDetailView,
    ClosedEnquiryListView,
    ActiveEnquiryListView,
    EnquirySummaryByTelecaller,
    EnquiryStatisticsView,
)

urlpatterns = [
    # General Enquiry View (list/create all enquiries)
    path('enquiries/', EnquiryListCreateView.as_view(), name='enquiry-list-create'),

    # Detail View (retrieve/update/delete)
    path('enquiries/<int:pk>/', EnquiryDetailView.as_view(), name='enquiry-detail'),

    # Active enquiries only
    path('enquiries/active/', ActiveEnquiryListView.as_view(), name='enquiry-active'),

    # Closed enquiries only
    path('enquiries/closed/', ClosedEnquiryListView.as_view(), name='enquiry-closed'),

    # Telecaller-wise summary
    path('enquiries/summary/', EnquirySummaryByTelecaller.as_view(), name='enquiry-summary'),

    # Overall statistics view
    path('enquiries/statistics/', EnquiryStatisticsView.as_view(), name='enquiry-statistics'),


    
]
