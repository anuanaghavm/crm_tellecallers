from django.urls import path
from .views import (
    TelecallerListCreateView,
    TelecallerDetailView
)

urlpatterns = [
    path('telecallers/', TelecallerListCreateView.as_view(), name='telecaller-list-create'),
    path('telecallers/<int:pk>/', TelecallerDetailView.as_view(), name='telecaller-detail'),
]
