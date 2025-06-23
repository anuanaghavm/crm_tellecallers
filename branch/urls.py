from django.urls import path
from .views import BranchListCreateView, BranchRetrieveUpdateDestroyView,BranchTotalCountAPIView

urlpatterns = [
    path('branches/', BranchListCreateView.as_view(), name='branch-list-create'),  # List and create branches
    path('branches/<int:pk>/', BranchRetrieveUpdateDestroyView.as_view(), name='branch-retrieve-update-destroy'),  # Retrieve, update, delete a branch
    path('branches-count/', BranchTotalCountAPIView.as_view(), name='branc-status-counts'),

]
