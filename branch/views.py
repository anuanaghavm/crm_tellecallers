from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from .models import Branch
from .serializers import BranchSerializer
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView


class BranchPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "code": 200,
            "message": "",
            "data": data,
            "pagination": {
                "total": self.page.paginator.count,
                "page": self.page.number,
                "limit": self.get_page_size(self.request),
                "totalPages": self.page.paginator.num_pages,
            }
        })

class BranchListCreateView(ListCreateAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = BranchPagination  # Add this line for pagination
    
    def get_queryset(self):
        """Override to add search functionality"""
        queryset = Branch.objects.all().order_by('-id')
        search_query = self.request.query_params.get('search', '')
        
        if search_query:
            queryset = queryset.filter(branch_name__istartswith=search_query)
        
        return queryset
    
    def get_serializer_context(self):
        """Add context for serializer"""
        context = super().get_serializer_context()
        context['include_users'] = True
        return context


class BranchRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, and deleting a branch.
    """
    queryset = Branch.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return BranchSerializer
    
class BranchTotalCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_count = Branch.objects.count()

        return Response({
            "code": 200,
            "message": "",
            "data":{
            "total_Branches": total_count,
            }
        })