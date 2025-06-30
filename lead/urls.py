from django.urls import path
from .views import EnquiryListCreateView, EnquiryDetailView,WalkInEnquiryListView,FollowUpEnquiryListView,ClosedEnquiryListView,ActiveEnquiryListView,EnquirySummaryByTelecaller,EnquiryListWithoutPagination

urlpatterns = [
    path('enquiries/', EnquiryListCreateView.as_view(), name='enquiry-list-create'),
    path('enquiries/<int:pk>/', EnquiryDetailView.as_view(), name='enquiry-detail'),
    path('enquiries/walk-in-list/', WalkInEnquiryListView.as_view(), name='walk-in-enquiries-list'),
    path('enquiries/follow-up/', FollowUpEnquiryListView.as_view(), name='follow-up-enquiry-list'),
    path('enquiries/closed/', ClosedEnquiryListView.as_view(), name='closed-enquiry-list'),
    path('enquiries/active/', ActiveEnquiryListView.as_view(), name='active-enquiries'),
    path('enquiries-summary/', EnquirySummaryByTelecaller.as_view(), name='enquiry-summary-by-telecaller'),
    path('enquiries/all/', EnquiryListWithoutPagination.as_view(), name='enquiries-all'),

]