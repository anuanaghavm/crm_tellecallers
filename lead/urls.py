from django.urls import path
from .views import (
    LeadListCreateView,
    LeadRetrieveUpdateDestroyView,
    CallRegisterListCreateView,
    CallRegisterRetrieveUpdateDestroyView
)

urlpatterns = [
    path('leads/', LeadListCreateView.as_view(), name='lead-list-create'),
    path('leads/<int:pk>/', LeadRetrieveUpdateDestroyView.as_view(), name='lead-detail'),
    path('calls/', CallRegisterListCreateView.as_view(), name='call-list-create'),
    path('calls/<int:pk>/', CallRegisterRetrieveUpdateDestroyView.as_view(), name='call-detail'),
]
