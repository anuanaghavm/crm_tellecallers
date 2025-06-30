from rest_framework import status, filters as drf_filters
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from rest_framework.views import APIView
from tellecaller.models import Telecaller
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


# ✅ Shared FilterSet
class EnquiryBaseFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    enquiry_source = django_filters.CharFilter(field_name='enquiry_source', lookup_expr='iexact')
    branch = django_filters.NumberFilter(field_name='assigned_by__branch')
    branch_name = django_filters.CharFilter(field_name='assigned_by__branch__branch_name', lookup_expr='icontains')
    telecaller = django_filters.NumberFilter(field_name='assigned_by')
    telecaller_name = django_filters.CharFilter(field_name='assigned_by__name', lookup_expr='icontains')

    class Meta:
        model = Enquiry
        fields = ['enquiry_source', 'branch', 'branch_name', 'telecaller', 'telecaller_name', 'start_date', 'end_date']


# ✅ Base View
class BaseEnquiryListCreateView(ListCreateAPIView):
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_class = EnquiryBaseFilter
    search_fields = ['candidate_name', 'email', 'phone', 'assigned_by__branch__branch_name']
    enquiry_status = None

    def get_queryset(self):
        return Enquiry.objects.filter(enquiry_status=self.enquiry_status).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        instance_id = response.data.get('id')
        if instance_id:
            instance = Enquiry.objects.get(pk=instance_id)
            serializer = self.get_serializer(instance)
        else:
            serializer = response

        return Response({
            "code": 201,
            "message": f"{self.enquiry_status} enquiry created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


# ✅ Enquiry Status Views
class WalkInEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'walk_in_list'


class FollowUpEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Follow Up'


class ClosedEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Closed'


class ActiveEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Active'


# ✅ Main ListCreate View (Active enquiries only)
class EnquiryListCreateView(ListCreateAPIView):
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_class = EnquiryBaseFilter
    search_fields = ['candidate_name', 'email', 'phone', 'assigned_by__branch__branch_name']

    def get_queryset(self):
        return Enquiry.objects.filter(enquiry_status='Active').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        instance_id = response.data.get('id')
        if instance_id:
            instance = Enquiry.objects.get(pk=instance_id)
            serializer = self.get_serializer(instance)
        else:
            serializer = response

        return Response({
            "code": 201,
            "message": "Enquiry created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


# ✅ Retrieve, Update, Delete View
class EnquiryDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# ✅ Summary by Telecaller
class EnquirySummaryByTelecaller(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        data = []

        for telecaller in Telecaller.objects.all():
            enquiries = Enquiry.objects.filter(assigned_by=telecaller)
            summary = {
                "telecaller_id": telecaller.id,
                "telecaller_name": telecaller.name,
                "total_enquiries": enquiries.count(),
                "contacted": enquiries.filter(enquiry_status="contacted").count(),
                "not_contacted": enquiries.exclude(enquiry_status="contacted").count(),
                "answered": enquiries.filter(enquiry_status="Answered").count(),
                "not_answered": enquiries.filter(enquiry_status="Not Answered").count(),
                "walkin": enquiries.filter(enquiry_status="walk_in_list").count(),
                "followup": enquiries.filter(enquiry_status="Follow Up").count(),
                "positive": enquiries.filter(feedback__icontains="positive").count(),
                "negative": enquiries.filter(feedback__icontains="negative").count(),
            }
            data.append(summary)

        return Response({
            "code": 200,
            "message": "Enquiry summary fetched successfully",
            "data": data
        })
