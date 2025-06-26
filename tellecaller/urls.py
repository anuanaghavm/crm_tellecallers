from django.urls import path
from .views import (
    TelecallerListCreateView,
    TelecallerDetailView
)

urlpatterns = [
    path('telecallers/', TelecallerListCreateView.as_view(), name='telecaller-list-create'),
    path('telecallers/<uuid:uuid>/', TelecallerDetailView.as_view(), name='telecaller-detail'),
]
