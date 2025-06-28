from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from .models import Enquiry
from .serializers import EnquirySerializer

# ✅ Custom Pagination
class CustomPagination(PageNumberPagination):
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



class WalkInEnquiryFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    enquiry_source = django_filters.CharFilter(field_name='enquiry_source', lookup_expr='iexact')
    telecaller_id = django_filters.NumberFilter(field_name='telecaller_id')
    branch = django_filters.NumberFilter(field_name='branch_id')

    class Meta:
        model = Enquiry
        fields = ['enquiry_source', 'branch', 'telecaller_id', 'start_date', 'end_date']




# ✅ FilterSet for Active Enquiries
class ActiveEnquiryFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    enquiry_source = django_filters.CharFilter(field_name='enquiry_source', lookup_expr='iexact')
    branch = django_filters.NumberFilter(field_name='branch_id')

    class Meta:
        model = Enquiry
        fields = ['enquiry_source', 'branch', 'start_date', 'end_date']

# ✅ Enquiry List & Create View (only Active enquiries)
class EnquiryListCreateView(ListCreateAPIView):
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_class = ActiveEnquiryFilter
    search_fields = ['candidate_name', 'email', 'phone', 'branch__branch_name']

    def get_queryset(self):
        return Enquiry.objects.filter(enquiry_status='Active').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "code": 201,
            "message": "Enquiry created successfully",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

# ✅ Detail View (with all enquiries — no status filtering)
class EnquiryDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]





# ✅ Walk-in Enquiry List View
class WalkInEnquiryListView(ListCreateAPIView):
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_class = WalkInEnquiryFilter
    search_fields = ['candidate_name', 'email', 'phone', 'branch__branch_name']

    def get_queryset(self):
        # Return only walk-in enquiries (you can customize the condition if needed)
        return Enquiry.objects.filter(enquiry_source__iexact='Walk-In').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "code": 201,
            "message": "Walk-in enquiry created successfully",
            "data": response.data
        }, status=status.HTTP_201_CREATED)
