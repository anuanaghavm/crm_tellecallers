from rest_framework import status, filters as drf_filters
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from rest_framework.views import APIView
from django.db.models import Q
from tellecaller.models import Telecaller
from .models import Enquiry
from .serializers import EnquirySerializer


# ✅ Unified Pagination
class LeadsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "code": 200,
            "message": "Data fetched successfully",
            "data": data,
            "pagination": {
                "total": self.page.paginator.count,
                "page": self.page.number,
                "limit": self.get_page_size(self.request),
                "totalPages": self.page.paginator.num_pages,
                "hasNext": self.page.has_next(),
                "hasPrevious": self.page.has_previous(),
            }
        })


# ✅ Enhanced FilterSet
class EnquiryBaseFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    enquiry_source = django_filters.CharFilter(field_name='enquiry_source', lookup_expr='iexact')
    branch = django_filters.NumberFilter(field_name='assigned_by__branch')
    branch_name = django_filters.CharFilter(field_name='assigned_by__branch__branch_name', lookup_expr='icontains')
    telecaller = django_filters.NumberFilter(field_name='assigned_by')
    telecaller_name = django_filters.CharFilter(field_name='assigned_by__name', lookup_expr='icontains')
    enquiry_status = django_filters.CharFilter(field_name='enquiry_status', lookup_expr='iexact')

    class Meta:
        model = Enquiry
        fields = ['enquiry_source', 'branch', 'branch_name', 'telecaller', 'telecaller_name', 'enquiry_status', 'start_date', 'end_date']


# ✅ Enhanced Base View for Status-based Views
class BaseEnquiryListCreateView(ListCreateAPIView):
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LeadsPagination
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_class = EnquiryBaseFilter
    search_fields = ['candidate_name', 'email', 'phone', 'assigned_by__branch__branch_name', 'assigned_by__name']
    enquiry_status = None

    def get_queryset(self):
        if self.enquiry_status:
            return Enquiry.objects.filter(enquiry_status=self.enquiry_status).order_by('-created_at')
        return Enquiry.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        # Set the enquiry_status if specified and not already set
        if self.enquiry_status and not serializer.validated_data.get('enquiry_status'):
            serializer.save(
                created_by=self.request.user,
                enquiry_status=self.enquiry_status
            )
        else:
            serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            "code": 201,
            "message": f"{'Enquiry' if not self.enquiry_status else self.enquiry_status.replace('_', ' ').title()} created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Check if pagination is disabled
        if request.query_params.get('no_pagination', '').lower() in ['true', '1']:
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "code": 200,
                "message": "Data fetched successfully",
                "data": serializer.data,
                "total": queryset.count()
            })
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "code": 200,
            "message": "Data fetched successfully",
            "data": serializer.data,
            "total": queryset.count()
        })


# ✅ Status-Specific Views
class WalkInEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'walk_in_list'


class FollowUpEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Follow Up'


class ClosedEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Closed'


class ActiveEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Active'


class ContactedEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'contacted'


class AnsweredEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Answered'


class NotAnsweredEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Not Answered'


# ✅ General Enquiry View (All statuses, defaults to Active for creation)
class EnquiryListCreateView(BaseEnquiryListCreateView):
    def get_queryset(self):
        # Show all enquiries by default, but can be filtered
        return Enquiry.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        # Default to 'Active' status if not specified
        if not serializer.validated_data.get('enquiry_status'):
            serializer.save(
                created_by=self.request.user,
                enquiry_status='Active'
            )
        else:
            serializer.save(created_by=self.request.user)


# ✅ Retrieve / Update / Delete View
class EnquiryDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "code": 200,
            "message": "Enquiry details fetched successfully",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            "code": 200,
            "message": "Enquiry updated successfully",
            "data": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "code": 200,
            "message": "Enquiry deleted successfully"
        }, status=status.HTTP_200_OK)


# ✅ Enhanced Summary by Telecaller
class EnquirySummaryByTelecaller(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        # Apply date filters if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        branch_id = request.query_params.get('branch')
        
        data = []
        telecallers = Telecaller.objects.all()
        
        if branch_id:
            telecallers = telecallers.filter(branch_id=branch_id)

        for telecaller in telecallers:
            enquiries = Enquiry.objects.filter(assigned_by=telecaller)
            
            # Apply date filters
            if start_date:
                enquiries = enquiries.filter(created_at__gte=start_date)
            if end_date:
                enquiries = enquiries.filter(created_at__lte=end_date)
            
            summary = {
                "telecaller_id": telecaller.id,
                "telecaller_name": telecaller.name,
                "branch_name": telecaller.branch.branch_name if hasattr(telecaller, 'branch') and telecaller.branch else None,
                "total_enquiries": enquiries.count(),
                "active": enquiries.filter(enquiry_status="Active").count(),
                "contacted": enquiries.filter(enquiry_status="contacted").count(),
                "not_contacted": enquiries.exclude(enquiry_status="contacted").count(),
                "answered": enquiries.filter(enquiry_status="Answered").count(),
                "not_answered": enquiries.filter(enquiry_status="Not Answered").count(),
                "walkin": enquiries.filter(enquiry_status="walk_in_list").count(),
                "followup": enquiries.filter(enquiry_status="Follow Up").count(),
                "closed": enquiries.filter(enquiry_status="Closed").count(),
                "positive": enquiries.filter(feedback__icontains="positive").count(),
                "negative": enquiries.filter(feedback__icontains="negative").count(),
            }
            data.append(summary)

        return Response({
            "code": 200,
            "message": "Enquiry summary fetched successfully",
            "data": data,
            "total_telecallers": len(data)
        })


# ✅ Simplified Non-Paginated View (now handled by base view with query param)
class EnquiryListWithoutPagination(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        # This view is now redundant as the base view handles no_pagination=true
        # But keeping for backward compatibility
        queryset = Enquiry.objects.all().order_by('-created_at')

        # Apply filters
        filterset = EnquiryBaseFilter(request.GET, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs

        # Apply search
        search_query = request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(candidate_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(assigned_by__name__icontains=search_query) |
                Q(assigned_by__branch__branch_name__icontains=search_query)
            )

        serializer = EnquirySerializer(queryset, many=True)
        return Response({
            "code": 200,
            "message": "All enquiries fetched successfully (no pagination)",
            "data": serializer.data,
            "total": queryset.count()
        })


# ✅ Enquiry Statistics View
class EnquiryStatisticsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        # Apply date filters if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        branch_id = request.query_params.get('branch')
        
        queryset = Enquiry.objects.all()
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if branch_id:
            queryset = queryset.filter(assigned_by__branch_id=branch_id)

        stats = {
            "total_enquiries": queryset.count(),
            "active": queryset.filter(enquiry_status="Active").count(),
            "contacted": queryset.filter(enquiry_status="contacted").count(),
            "answered": queryset.filter(enquiry_status="Answered").count(),
            "not_answered": queryset.filter(enquiry_status="Not Answered").count(),
            "walkin": queryset.filter(enquiry_status="walk_in_list").count(),
            "followup": queryset.filter(enquiry_status="Follow Up").count(),
            "closed": queryset.filter(enquiry_status="Closed").count(),
            "positive_feedback": queryset.filter(feedback__icontains="positive").count(),
            "negative_feedback": queryset.filter(feedback__icontains="negative").count(),
        }

        return Response({
            "code": 200,
            "message": "Enquiry statistics fetched successfully",
            "data": stats
        })