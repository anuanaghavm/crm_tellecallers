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
from .models import Enquiry, Mettad, Course, Service
from .serializers import EnquirySerializer, MettadSerializer, CourseSerializer, ServiceSerializer
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from rest_framework import status
import pandas as pd
from .models import Enquiry, Mettad, Course, Service
from tellecaller.models import Telecaller
from rest_framework.parsers import MultiPartParser
from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

# ✅ Pagination
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

# ✅ Updated Filter with Mettad
class EnquiryBaseFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    enquiry_source = django_filters.CharFilter(field_name='enquiry_source', lookup_expr='iexact')
    branch = django_filters.NumberFilter(field_name='assigned_by__branch')
    branch_name = django_filters.CharFilter(field_name='assigned_by__branch__branch_name', lookup_expr='icontains')
    telecaller = django_filters.NumberFilter(field_name='assigned_by')
    telecaller_name = django_filters.CharFilter(field_name='assigned_by__name', lookup_expr='icontains')
    enquiry_status = django_filters.CharFilter(field_name='enquiry_status', lookup_expr='iexact')
    
    # Mettad filters
    mettad = django_filters.NumberFilter(field_name='Mettad')
    mettad_name = django_filters.CharFilter(field_name='Mettad__name', lookup_expr='icontains')

    class Meta:
        model = Enquiry
        fields = ['enquiry_source', 'branch', 'branch_name', 'telecaller', 'telecaller_name', 
                 'enquiry_status', 'start_date', 'end_date', 'mettad', 'mettad_name']

# ✅ Base View (Updated search fields)
class BaseEnquiryListCreateView(ListCreateAPIView):
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LeadsPagination
    filterset_class = EnquiryBaseFilter

    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    search_fields = [
        'candidate_name',
        'email',
        'phone',
        'assigned_by__branch__branch_name',
        'assigned_by__name',
        'Mettad__name'
    ]

    def get_queryset(self):
        if self.enquiry_status:
            return Enquiry.objects.filter(enquiry_status=self.enquiry_status).select_related('Mettad', 'assigned_by__branch').order_by('-created_at')
        return Enquiry.objects.all().select_related('Mettad', 'assigned_by__branch').order_by('-created_at')

    def perform_create(self, serializer):
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

        if request.query_params.get('no_pagination', '').lower() in ['true', '1']:
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "code": 200,
                "message": "Data fetched successfully",
                "data": serializer.data,
                "total": queryset.count()
            })

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

# ✅ Mettad List/Create View
class MettadListCreateView(ListCreateAPIView):
    queryset = Mettad.objects.all().order_by('name')
    serializer_class = MettadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [drf_filters.SearchFilter]
    search_fields = ['name']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response({
            "code": 201,
            "message": "Mettad created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "code": 200,
            "message": "Mettads fetched successfully",
            "data": serializer.data,
            "total": queryset.count()
        })

# ✅ Mettad Detail View
class MettadDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Mettad.objects.all()
    serializer_class = MettadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "code": 200,
            "message": "Mettad details fetched successfully",
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
            "message": "Mettad updated successfully",
            "data": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "code": 200,
            "message": "Mettad deleted successfully"
        }, status=status.HTTP_200_OK)

# ✅ Course CRUD Operations
class CourseListCreateView(ListCreateAPIView):
    queryset = Course.objects.all().order_by('name')
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [drf_filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        queryset = Course.objects.all().order_by('name')
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response({
            "code": 201,
            "message": "Course created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "code": 200,
            "message": "Courses fetched successfully",
            "data": serializer.data,
            "total": queryset.count()
        })

class CourseDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "code": 200,
            "message": "Course details fetched successfully",
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
            "message": "Course updated successfully",
            "data": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if course is being used in any enquiries
        if instance.enquiries.exists():
            return Response({
                "code": 400,
                "message": "Cannot delete course. It is being used in enquiries."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_destroy(instance)
        return Response({
            "code": 200,
            "message": "Course deleted successfully"
        }, status=status.HTTP_200_OK)

# ✅ Service CRUD Operations
class ServiceListCreateView(ListCreateAPIView):
    queryset = Service.objects.all().order_by('name')
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [drf_filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        queryset = Service.objects.all().order_by('name')
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response({
            "code": 201,
            "message": "Service created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "code": 200,
            "message": "Services fetched successfully",
            "data": serializer.data,
            "total": queryset.count()
        })

class ServiceDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "code": 200,
            "message": "Service details fetched successfully",
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
            "message": "Service updated successfully",
            "data": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if service is being used in any enquiries
        if instance.enquiries.exists():
            return Response({
                "code": 400,
                "message": "Cannot delete service. It is being used in enquiries."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_destroy(instance)
        return Response({
            "code": 200,
            "message": "Service deleted successfully"
        }, status=status.HTTP_200_OK)

# ✅ Additional utility views for getting only active courses/services
class ActiveCourseListView(ListCreateAPIView):
    queryset = Course.objects.filter(is_active=True).order_by('name')
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [drf_filters.SearchFilter]
    search_fields = ['name']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "code": 200,
            "message": "Active courses fetched successfully",
            "data": serializer.data,
            "total": queryset.count()
        })

class ActiveServiceListView(ListCreateAPIView):
    queryset = Service.objects.filter(is_active=True).order_by('name')
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [drf_filters.SearchFilter]
    search_fields = ['name']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "code": 200,
            "message": "Active services fetched successfully",
            "data": serializer.data,
            "total": queryset.count()
        })

# ✅ Active & Closed Enquiry Views (same as before)
class ActiveEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Active'

class ClosedEnquiryListView(BaseEnquiryListCreateView):
    enquiry_status = 'Closed'

# ✅ General Enquiry View (same as before)
class EnquiryListCreateView(BaseEnquiryListCreateView):
    def get_queryset(self):
        user = self.request.user
        role = getattr(user.role, 'name', None)

        queryset = Enquiry.objects.all()

        # Filter based on logged-in telecaller
        if role != 'Admin':
            telecaller = Telecaller.objects.filter(account=user).first()
            if telecaller:
                queryset = queryset.filter(assigned_by=telecaller)
            else:
                return Enquiry.objects.none()

        # ✅ Use getattr to avoid AttributeError
        enquiry_status = getattr(self, 'enquiry_status', None)
        if enquiry_status:
            queryset = queryset.filter(enquiry_status=enquiry_status)

        return queryset.select_related('Mettad', 'assigned_by__branch').order_by('-created_at')

    def perform_create(self, serializer):
        enquiry_status = getattr(self, 'enquiry_status', None)
        if enquiry_status and not serializer.validated_data.get('enquiry_status'):
            serializer.save(
                created_by=self.request.user,
                enquiry_status=enquiry_status
            )
        else:
            serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        enquiry_status = getattr(self, 'enquiry_status', None)
        status_msg = enquiry_status.replace('_', ' ').title() if enquiry_status else "Enquiry"

        return Response({
            "code": 201,
            "message": f"{status_msg} created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

# ✅ Retrieve / Update / Delete (same as before)
class EnquiryDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Enquiry.objects.all().select_related('Mettad', 'assigned_by__branch')
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

# ✅ Summary by Telecaller (Updated to include Mettad info)
class EnquirySummaryByTelecaller(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        branch_id = request.query_params.get('branch')
        mettad_id = request.query_params.get('mettad')

        data = []
        telecallers = Telecaller.objects.all()

        if branch_id:
            telecallers = telecallers.filter(branch_id=branch_id)

        for telecaller in telecallers:
            enquiries = Enquiry.objects.filter(assigned_by=telecaller)

            if start_date:
                enquiries = enquiries.filter(created_at__gte=start_date)
            if end_date:
                enquiries = enquiries.filter(created_at__lte=end_date)
            if mettad_id:
                enquiries = enquiries.filter(Mettad_id=mettad_id)

            summary = {
                "telecaller_id": telecaller.id,
                "telecaller_name": telecaller.name,
                "branch_name": telecaller.branch.branch_name if hasattr(telecaller, 'branch') and telecaller.branch else None,
                "total_enquiries": enquiries.count(),
                "active": enquiries.filter(enquiry_status="Active").count(),
                "closed": enquiries.filter(enquiry_status="Closed").count(),
            }
            data.append(summary)

        return Response({
            "code": 200,
            "message": "Enquiry summary fetched successfully",
            "data": data,
            "total_telecallers": len(data)
        })

# ✅ Enquiry Statistics (Updated to include Mettad filter)
class EnquiryStatisticsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        branch_id = request.query_params.get('branch')
        mettad_id = request.query_params.get('mettad')

        queryset = Enquiry.objects.all()

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if branch_id:
            queryset = queryset.filter(assigned_by__branch_id=branch_id)
        if mettad_id:
            queryset = queryset.filter(Mettad_id=mettad_id)

        stats = {
            "total_enquiries": queryset.count(),
            "active": queryset.filter(enquiry_status="Active").count(),
            "closed": queryset.filter(enquiry_status="Closed").count(),
        }

        return Response({
            "code": 200,
            "message": "Enquiry statistics fetched successfully",
            "data": stats
        })
    






class EnquiryImportAPIView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"message": "No file uploaded"}, status=400)

        try:
            df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        except Exception as e:
            return Response({"code": 400, "message": f"Failed to read file: {str(e)}"}, status=400)

        # ✅ Fetch all telecallers
        telecallers = list(Telecaller.objects.all())
        total_telecallers = len(telecallers)
        telecaller_index = 0

        created = []
        warnings = []

        for idx, row in df.iterrows():
            try:
                # ✅ Round-robin telecaller assignment
                assigned_by = telecallers[telecaller_index] if total_telecallers > 0 else None
                telecaller_index = (telecaller_index + 1) % total_telecallers

                preferred_course = None
                if pd.notna(row.get('Preferred Course')):
                    preferred_course = Course.objects.filter(name=row['Preferred Course']).first()
                    if not preferred_course:
                        warnings.append(f"Row {idx + 2}: Course '{row['Preferred Course']}' not found.")

                required_service = None
                if pd.notna(row.get('Service')):
                    required_service = Service.objects.filter(name=row['Service']).first()
                    if not required_service:
                        warnings.append(f"Row {idx + 2}: Service '{row['Service']}' not found.")

                enquiry = Enquiry.objects.create(
                    candidate_name=row['Name'],
                    phone=row['Phone'],
                    email=row.get('Email', ''),
                    preferred_course=preferred_course,
                    required_service=required_service,
                    enquiry_status='Active',
                    feedback=None,
                    follow_up_on=None,
                    created_by=request.user,
                    assigned_by=assigned_by,
                )
                created.append(enquiry)

            except Exception as e:
                warnings.append(f"Row {idx + 2}: Failed - {str(e)}")

        return Response({
            "code": 201 if created else 207,
            "message": f"{len(created)} enquiries imported successfully",
            "successfully_imported": len(created),
            "warnings": warnings
        }, status=201 if created else 207)
