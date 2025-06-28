from django.urls import path
from .views import EnquiryListCreateView, EnquiryDetailView,WalkInEnquiryListView

urlpatterns = [
    path('enquiries/', EnquiryListCreateView.as_view(), name='enquiry-list-create'),
    path('enquiries/<int:pk>/', EnquiryDetailView.as_view(), name='enquiry-detail'),
    path('enquiries/walkin/', WalkInEnquiryListView.as_view(), name='walkin-enquiry-list'),

]
