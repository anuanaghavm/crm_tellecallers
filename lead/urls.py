from django.urls import path
from .views import EnquiryListCreateView, EnquiryDetailView,WalkInEnquiryListView

urlpatterns = [
    path('enquiries/', EnquiryListCreateView.as_view(), name='enquiry-list-create'),
    path('enquiries/<int:pk>/', EnquiryDetailView.as_view(), name='enquiry-detail'),
    path('enquiries/walk-in-list/', WalkInEnquiryListView.as_view(), name='walk-in-enquiries-list'),

]
