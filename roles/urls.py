from django.urls import path
from .views import RoleListCreateView,RoleRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('roles/', RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<int:pk>/',RoleRetrieveUpdateDestroyAPIView.as_view(),name='role-list-retrieve-update-destroy'),
]