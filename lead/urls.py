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
    CourseListCreateView,
    CourseDetailView,
    ActiveCourseListView,
    ServiceListCreateView,
    ServiceDetailView,
    EnquiryImportAPIView,
    ActiveServiceListView,
    ChecklistListCreateView,
    MetaConversionAPIView,
    ChecklistDetailView
)

urlpatterns = [
    # Enquiry URLs
    path('enquiries/', EnquiryListCreateView.as_view(), name='enquiry-list-create'),
    path('enquiries/active/', ActiveEnquiryListView.as_view(), name='active-enquiry-list'),
    path('enquiries/closed/', ClosedEnquiryListView.as_view(), name='closed-enquiry-list'),
    path('enquiries/<int:pk>/', EnquiryDetailView.as_view(), name='enquiry-detail'),
    path('enquiries/summary/', EnquirySummaryByTelecaller.as_view(), name='enquiry-summary'),
    path('enquiries/statistics/', EnquiryStatisticsView.as_view(), name='enquiry-statistics'),
    path('courses/', CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('courses/active/', ActiveCourseListView.as_view(), name='active-course-list'),
    path('services/', ServiceListCreateView.as_view(), name='service-list-create'),
    path('services/<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),
    path('services/active/', ActiveServiceListView.as_view(), name='active-service-list'),
    path('enquiries/import/', EnquiryImportAPIView.as_view(), name='enquiry-import'),
    path('meta-conversion/', MetaConversionAPIView.as_view(), name='meta-conversion'),

    path('checklists/', ChecklistListCreateView.as_view(), name='checklist-list'),
    path('checklists/<int:pk>/', ChecklistDetailView.as_view(), name='checklist-detail'),

    # Mettad URLs
    path('mettads/', MettadListCreateView.as_view(), name='mettad-list-create'),
    path('mettads/<int:pk>/', MettadDetailView.as_view(), name='mettad-detail'),
]