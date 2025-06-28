from rest_framework import status, filters as drf_filters
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
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

# ✅ Shared FilterSet for Walk-in, Follow-up, Closed, Active
class EnquiryBaseFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    enquiry_source = django_filters.CharFilter(field_name='enquiry_source', lookup_expr='iexact')
    branch_id = django_filters.NumberFilter(field_name='branch_id')
    branch_name = django_filters.CharFilter(field_name='branch__branch_name', lookup_expr='icontains')
    telecaller_id = django_filters.NumberFilter(field_name='telecaller_id')
    telecaller_name = django_filters.CharFilter(field_name='telecaller__name', lookup_expr='icontains')

    class Meta:
        model = Enquiry
        fields = [
            'enquiry_source',
            'branch_id',
            'branch_name',
            'telecaller_id',
            'telecaller_name',
            'start_date',
            'end_date',
        ]

# ✅ Base View to reduce duplication
class BaseEnquiryListCreateView(ListCreateAPIView):
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_class = EnquiryBaseFilter
    search_fields = ['candidate_name', 'email', 'phone', 'branch__branch_name']
    enquiry_status = None  # To be set in subclasses

    def get_queryset(self):
        return Enquiry.objects.filter(enquiry_status=self.enquiry_status).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "code": 201,
            "message": f"{self.enquiry_status} enquiry created successfully",
            "data": response.data
        }, status=status.HTTP_201_CREATED)

# ✅ Individual Views
class WalkInEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'walk_in_list'

class FollowUpEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Follow Up'

class ClosedEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Closed'

class ActiveEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Active'

# ✅ Separate List View for All Enquiries (only Active by default)
class EnquiryListCreateView(ListCreateAPIView):
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_fields = ['enquiry_source', 'branch_id']  # Minimal fields
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

# ✅ Retrieve, Update, Destroy View
class EnquiryDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]