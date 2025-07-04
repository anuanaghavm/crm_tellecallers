from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response    
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone   
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter 
from .serializers import CallRegisterSerializer
from .models import CallRegister
from lead.models import Enquiry
from tellecaller.models import Telecaller
from datetime import timedelta
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView ,GenericAPIView
from rest_framework import serializers
from collections import defaultdict

# ✅ Custom Pagination Class
class callsPagination(PageNumberPagination):
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

# ✅ List and Create Call Logs
class CallRegisterListCreateView(generics.ListCreateAPIView):
    serializer_class = CallRegisterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['call_type', 'call_status', 'call_outcome', 'enquiry__enquiry_status']
    search_fields = ['enquiry__candidate_name', 'enquiry__phone', 'notes']
    ordering_fields = ['call_start_time', 'created_at', 'call_duration']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.role and user.role.name == 'Admin':
            queryset = CallRegister.objects.select_related(
                'enquiry', 'telecaller', 'telecaller__branch'
            ).all()
        else:
            try:
                telecaller = Telecaller.objects.get(account=user)
                queryset = CallRegister.objects.select_related(
                    'enquiry', 'telecaller', 'telecaller__branch'
                ).filter(telecaller=telecaller)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()
        
        # Custom filtering for call outcomes
        call_outcome = self.request.query_params.get('call_outcome', None)
        if call_outcome:
            queryset = queryset.filter(call_outcome=call_outcome)
            
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ Follow Up Calls View with Pagination
class FollowUpCallsView(generics.ListAPIView):
    serializer_class = CallRegisterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['enquiry__candidate_name', 'enquiry__phone', 'notes']
    ordering_fields = ['call_start_time', 'created_at', 'follow_up_date']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        base_queryset = CallRegister.objects.select_related(
            'enquiry', 'telecaller', 'telecaller__branch'
        ).filter(call_outcome='Follow Up')

        if user.role and user.role.name != 'Admin':
            try:
                telecaller = Telecaller.objects.get(account=user)
                base_queryset = base_queryset.filter(telecaller=telecaller)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()

        # ✅ Optional Filters
        branch_name = self.request.query_params.get('branch_name')
        telecaller_name = self.request.query_params.get('telecaller_name')
        enquiry_date = self.request.query_params.get('enquiry_date')
        enquiry_status = self.request.query_params.get('enquiry_status')
        follow_up_date = self.request.query_params.get('follow_up_date')
        pending_only = self.request.query_params.get('pending_only')

        if branch_name:
            base_queryset = base_queryset.filter(
                telecaller__branch__branch_name__icontains=branch_name
            )
        if telecaller_name:
            base_queryset = base_queryset.filter(
                telecaller__name__icontains=telecaller_name
            )
        if enquiry_date:
            base_queryset = base_queryset.filter(
                enquiry__created_at__date=enquiry_date
            )
        if enquiry_status:
            base_queryset = base_queryset.filter(
                enquiry__enquiry_status__iexact=enquiry_status
            )
        if follow_up_date:
            base_queryset = base_queryset.filter(
                follow_up_date=follow_up_date
            )
        if pending_only and pending_only.lower() == 'true':
            today = timezone.now().date()
            base_queryset = base_queryset.filter(follow_up_date__lte=today)

        return base_queryset

# ✅ Walk-in List View with Pagination
class WalkInListView(generics.ListAPIView):
    serializer_class = CallRegisterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['enquiry__candidate_name', 'enquiry__phone', 'notes']
    ordering_fields = ['call_start_time', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        base_queryset = CallRegister.objects.select_related(
            'enquiry', 'telecaller', 'telecaller__branch'
        ).filter(call_outcome='walk_in_list')

        if user.role and user.role.name != 'Admin':
            try:
                telecaller = Telecaller.objects.get(account=user)
                base_queryset = base_queryset.filter(telecaller=telecaller)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()

        # ✅ Optional Filters
        branch_name = self.request.query_params.get('branch_name')
        telecaller_name = self.request.query_params.get('telecaller_name')
        enquiry_date = self.request.query_params.get('enquiry_date')
        enquiry_status = self.request.query_params.get('enquiry_status')

        if branch_name:
            base_queryset = base_queryset.filter(
                telecaller__branch__branch_name__icontains=branch_name
            )
        if telecaller_name:
            base_queryset = base_queryset.filter(
                telecaller__name__icontains=telecaller_name
            )
        if enquiry_date:
            base_queryset = base_queryset.filter(
                enquiry__created_at__date=enquiry_date
            )
        if enquiry_status:
            base_queryset = base_queryset.filter(
                enquiry__enquiry_status__iexact=enquiry_status
            )

        return base_queryset
# ✅ Call Outcome Filter View (Generic for all outcomes)
class CallOutcomeFilterView(generics.ListAPIView):
    serializer_class = CallRegisterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['enquiry__candidate_name', 'enquiry__phone', 'notes']
    ordering_fields = ['call_start_time', 'created_at', 'call_duration']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        outcome = self.kwargs.get('outcome')  # Get outcome from URL parameter
        
        if user.role and user.role.name == 'Admin':
            queryset = CallRegister.objects.select_related(
                'enquiry', 'telecaller', 'telecaller__branch'
            ).all()
        else:
            try:
                telecaller = Telecaller.objects.get(account=user)
                queryset = CallRegister.objects.select_related(
                    'enquiry', 'telecaller', 'telecaller__branch'
                ).filter(telecaller=telecaller)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()
        
        # Filter by outcome if provided
        if outcome:
            queryset = queryset.filter(call_outcome=outcome)
            
        return queryset

# ✅ Retrieve, Update, or Delete Call Log
class CallRegisterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CallRegisterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role and user.role.name == 'Admin':
            return CallRegister.objects.select_related(
                'enquiry', 'telecaller', 'telecaller__branch'
            ).all()
        try:
            telecaller = Telecaller.objects.get(account=user)
            return CallRegister.objects.select_related(
                'enquiry', 'telecaller', 'telecaller__branch'
            ).filter(telecaller=telecaller)
        except Telecaller.DoesNotExist:
            return CallRegister.objects.none()

# ✅ Telecaller Call Statistics View with Outcome Breakdown
class TelecallerCallStatsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            telecaller = Telecaller.objects.get(account=user)
        except Telecaller.DoesNotExist:
            return Response(
                {'error': 'Only telecallers can access call stats.'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        call_logs = CallRegister.objects.filter(telecaller=telecaller)
        today = timezone.now().date()
        today_calls = call_logs.filter(call_start_time__date=today)
        week_start = today - timedelta(days=today.weekday())
        week_calls = call_logs.filter(call_start_time__date__gte=week_start)
        month_calls = call_logs.filter(
            call_start_time__year=today.year,
            call_start_time__month=today.month
        )

        stats = {
            'total_calls': call_logs.count(),
            'today_calls': today_calls.count(),
            'week_calls': week_calls.count(),
            'month_calls': month_calls.count(),

            'connected_calls': call_logs.filter(call_status='contacted').count(),
            'not_answered_calls': call_logs.filter(call_status='Not Answered').count(),
            'busy_calls': call_logs.filter(call_status='Busy').count(),

            # Enhanced outcome statistics
            'interested_prospects': call_logs.filter(call_outcome='Interested').count(),
            'converted_leads': call_logs.filter(call_outcome='Converted').count(),
            'follow_ups_required': call_logs.filter(call_outcome='Follow Up').count(),
            'walk_in_list': call_logs.filter(call_outcome='walk_in_list').count(),
            'not_interested': call_logs.filter(call_outcome='Not Interested').count(),
            'callback_requested': call_logs.filter(call_outcome='Callback Requested').count(),
            'information_provided': call_logs.filter(call_outcome='Information Provided').count(),
            'do_not_call': call_logs.filter(call_outcome='Do Not Call').count(),

            'total_call_time': sum([log.call_duration or 0 for log in call_logs]),
            'today_call_time': sum([log.call_duration or 0 for log in today_calls]),

            'assigned_enquiries': Enquiry.objects.filter(assigned_by=telecaller).count(),
            'pending_follow_ups': call_logs.filter(
                call_outcome='Follow Up',
                follow_up_date__lte=today
            ).count(),
        }

        def format_time(seconds):
            if seconds:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                return f"{hours}h {minutes}m"
            return "0h 0m"

        stats['total_call_time_formatted'] = format_time(stats['total_call_time'])
        stats['today_call_time_formatted'] = format_time(stats['today_call_time'])

        if stats['connected_calls'] > 0:
            stats['conversion_rate'] = round(
                (stats['converted_leads'] / stats['connected_calls']) * 100, 2
            )
        else:
            stats['conversion_rate'] = 0

        return Response(stats)

# ✅ Telecaller Dashboard View
class TelecallerDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role and user.role.name == 'Admin':
            total_calls = CallRegister.objects.count()
            total_leads = Enquiry.objects.count()
            total_telecallers = Telecaller.objects.count()

            return Response({
                'dashboard_type': 'admin',
                'total_calls': total_calls,
                'total_leads': total_leads,
                'total_telecallers': total_telecallers,
            })

        # If telecaller
        try:
            telecaller = Telecaller.objects.get(account=user)
        except Telecaller.DoesNotExist:
            return Response(
                {'error': 'Only telecallers can access dashboard.'},
                status=status.HTTP_403_FORBIDDEN
            )

        today = timezone.now().date()

        total_calls = CallRegister.objects.filter(telecaller=telecaller).count()
        total_leads = Enquiry.objects.filter(assigned_by=telecaller).count()
        pending_followups = CallRegister.objects.filter(
            telecaller=telecaller,
            call_outcome='Follow Up',
            follow_up_date__lte=today
        ).count()
        walkin_count = CallRegister.objects.filter(
            telecaller=telecaller,
            call_outcome='walk_in_list'
        ).count()

        return Response({
            'dashboard_type': 'telecaller',
            'total_calls': total_calls,
            'total_leads': total_leads,
            'pending_followups': pending_followups,
            'walkin_list': walkin_count,
        })

    
class TelecallerCallSummaryView(ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination

    def get_queryset(self):
        if not self.request.user.role or self.request.user.role.name != 'Admin':
            return Telecaller.objects.none()  # empty queryset if not admin

        branch_name = self.request.query_params.get('branch_name', '').strip()
        telecaller_name = self.request.query_params.get('telecaller_name', '').strip()
        search_telecaller = self.request.query_params.get('search_telecaller_name', '').strip()

        telecallers = Telecaller.objects.select_related('branch').all()

        if branch_name:
            telecallers = telecallers.filter(branch__branch_name__icontains=branch_name)

        if telecaller_name:
            telecallers = telecallers.filter(name__icontains=telecaller_name)

        if search_telecaller:
            telecallers = telecallers.filter(name__istartswith=search_telecaller)

        return telecallers

    def list(self, request, *args, **kwargs):
        if not request.user.role or request.user.role.name != 'Admin':
            return Response({'error': 'Only admin can access this data.'}, status=403)

        queryset = self.paginate_queryset(self.get_queryset())

        response_data = []
        for telecaller in queryset:
            calls = CallRegister.objects.filter(telecaller=telecaller)

            summary = {
                'telecaller_id': telecaller.id,
                'telecaller_name': telecaller.name,
                'branch_name': telecaller.branch.branch_name if telecaller.branch else None,
                'total_calls': calls.count(),
                'total_follow_ups': calls.filter(call_outcome='Follow Up').count(),
                'contacted': calls.filter(call_status='contacted').count(),
                'not_contacted': calls.filter(call_status='not_contacted').count(),
                'answered': calls.filter(call_status='answered').count(),
                'not_answered': calls.filter(call_status='Not Answered').count(),
                'walk_in_list': calls.filter(call_outcome='walk_in_list').count(),
                'positive': calls.filter(call_outcome__in=['Interested', 'Converted']).count(),
                'negative': calls.filter(call_outcome__in=['Not Interested', 'Do Not Call']).count(),
            }

            response_data.append(summary)

        return self.get_paginated_response(response_data)

class AdminJobsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination
    serializer_class = serializers.Serializer  # Dummy serializer

    def get(self, request):
        if getattr(self, 'swagger_fake_view', False):
            return Response()

        user = request.user
        if not user.role or user.role.name != 'Admin':
            return Response({'error': 'Only admins can access this data.'}, status=403)

        filter_status = request.query_params.get("status")  # remaining/completed/None

        all_enquiries = Enquiry.objects.select_related('assigned_by__branch').order_by('-created_at')
        grouped_by_date = defaultdict(list)

        for enquiry in all_enquiries:
            assigned_date = enquiry.created_at.date()
            telecaller = enquiry.assigned_by

            call = CallRegister.objects.filter(enquiry=enquiry).first()
            has_outcome = call and call.call_outcome and call.call_outcome.strip() != ""

            # Filter by status
            if filter_status == "completed" and not has_outcome:
                continue
            if filter_status == "remining" and has_outcome:
                continue

            grouped_by_date[str(assigned_date)].append({
                "telecaller_id": telecaller.id,
                "telecaller_name": telecaller.name,
                "branch_name": telecaller.branch.branch_name if telecaller.branch else None,
                "enquiry_id": enquiry.id,
                "candidate_name": enquiry.candidate_name,
                "contact": enquiry.phone,
                "email": enquiry.email,
                "status": "Completed" if has_outcome else "Remaining",
                "outcome": call.call_outcome if call else None,
                "assigned_date": str(assigned_date)
            })

        grouped_response = []
        for date, leads in grouped_by_date.items():
            grouped_response.append({
                "assigned_date": date,
                "telecaller_jobs": leads
            })

        grouped_response.sort(key=lambda x: x["assigned_date"], reverse=True)

        # ✅ FIX: Use pagination properly
        page = self.paginate_queryset(grouped_response)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(grouped_response)

        
class TelecallerJobsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination

    def get(self, request):
        user = request.user
        try:
            telecaller = Telecaller.objects.get(account=user)
        except Telecaller.DoesNotExist:
            return Response({"error": "Only telecallers can access this."}, status=403)

        filter_status = request.query_params.get('status')  # remaining / completed / None
        all_leads = Enquiry.objects.filter(assigned_by=telecaller).order_by('-created_at')

        from collections import defaultdict
        grouped_data = defaultdict(list)

        for lead in all_leads:
            assigned_date = lead.created_at.date()
            call = CallRegister.objects.filter(enquiry=lead).first()
            has_outcome = call and call.call_outcome and call.call_outcome.strip() != ""

            # Filter by status
            if filter_status == "completed" and not has_outcome:
                continue
            if filter_status == "remining" and has_outcome:
                continue

            grouped_data[str(assigned_date)].append({
                "enquiry_id": lead.id,
                "name": lead.candidate_name,
                "contact": lead.phone,
                "email": lead.email,
                "status": "Completed" if has_outcome else "Remaining",
                "outcome": call.call_outcome if call else None
            })

        # Convert to list of date-wise group
        result = []
        for assigned_date, enquiries in grouped_data.items():
            result.append({
                "assigned_date": assigned_date,
                "leads": enquiries
            })

        result.sort(key=lambda x: x["assigned_date"], reverse=True)

        # ✅ FIX: Use pagination correctly
        page = self.paginate_queryset(result)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(result)


class NotAnsweredCallsView(generics.ListAPIView):
    serializer_class = CallRegisterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['enquiry__candidate_name', 'enquiry__phone', 'notes']
    ordering_fields = ['call_start_time', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        base_queryset = CallRegister.objects.select_related(
            'enquiry', 'telecaller', 'telecaller__branch'
        ).filter(call_status='Not Answered')

        if user.role and user.role.name != 'Admin':
            try:
                telecaller = Telecaller.objects.get(account=user)
                base_queryset = base_queryset.filter(telecaller=telecaller)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()

        # ✅ Optional Filters
        branch_name = self.request.query_params.get('branch_name')
        telecaller_name = self.request.query_params.get('telecaller_name')
        enquiry_date = self.request.query_params.get('enquiry_date')
        enquiry_status = self.request.query_params.get('enquiry_status')

        if branch_name:
            base_queryset = base_queryset.filter(
                telecaller__branch__branch_name__icontains=branch_name
            )
        if telecaller_name:
            base_queryset = base_queryset.filter(
                telecaller__name__icontains=telecaller_name
            )
        if enquiry_date:
            base_queryset = base_queryset.filter(
                enquiry__created_at__date=enquiry_date
            )
        if enquiry_status:
            base_queryset = base_queryset.filter(
                enquiry__enquiry_status__iexact=enquiry_status
            )

        return base_queryset
