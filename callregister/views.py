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
from rest_framework.views import APIView


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
        if user.role and user.role.name == 'Admin':
            queryset = CallRegister.objects.select_related(
                'enquiry', 'telecaller', 'telecaller__branch'
            ).filter(call_outcome='Follow Up')
        else:
            try:
                telecaller = Telecaller.objects.get(account=user)
                queryset = CallRegister.objects.select_related(
                    'enquiry', 'telecaller', 'telecaller__branch'
                ).filter(telecaller=telecaller, call_outcome='Follow Up')
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()
        
        # Additional filtering options
        follow_up_date = self.request.query_params.get('follow_up_date', None)
        if follow_up_date:
            queryset = queryset.filter(follow_up_date=follow_up_date)
            
        # Filter for pending follow-ups (due today or overdue)
        pending_only = self.request.query_params.get('pending_only', None)
        if pending_only and pending_only.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(follow_up_date__lte=today)
            
        return queryset

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
        if user.role and user.role.name == 'Admin':
            queryset = CallRegister.objects.select_related(
                'enquiry', 'telecaller', 'telecaller__branch'
            ).filter(call_outcome='walk_in_list')
        else:
            try:
                telecaller = Telecaller.objects.get(account=user)
                queryset = CallRegister.objects.select_related(
                    'enquiry', 'telecaller', 'telecaller__branch'
                ).filter(telecaller=telecaller, call_outcome='walk_in_list')
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()
                
        return queryset

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
        try:
            telecaller = Telecaller.objects.get(account=user)
        except Telecaller.DoesNotExist:
            return Response(
                {'error': 'Only telecallers can access dashboard.'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        today = timezone.now().date()

        # Pending follow-ups from CallRegister
        pending_followups_calls = CallRegister.objects.filter(
            telecaller=telecaller,
            call_outcome='Follow Up',
            follow_up_date__lte=today
        ).select_related('enquiry').values(
            'id', 'enquiry__candidate_name', 'enquiry__phone', 
            'follow_up_date', 'enquiry__preferred_course', 'notes'
        )

        # Walk-in list
        walk_in_list = CallRegister.objects.filter(
            telecaller=telecaller,
            call_outcome='walk_in_list'
        ).select_related('enquiry').values(
            'id', 'enquiry__candidate_name', 'enquiry__phone',
            'enquiry__preferred_course', 'call_start_time'
        )

        recent_calls = CallRegister.objects.filter(
            telecaller=telecaller
        ).select_related('enquiry').order_by('-created_at')[:10]

        recent_calls_data = []
        for call in recent_calls:
            recent_calls_data.append({
                'id': call.id,
                'candidate_name': call.enquiry.candidate_name,
                'call_status': call.call_status,
                'call_outcome': call.call_outcome,
                'call_start_time': call.call_start_time,
                'notes': call.notes,
            })

        new_enquiries = Enquiry.objects.filter(
            assigned_by=telecaller,
            created_at__date=today
        ).values('id', 'candidate_name', 'phone', 'preferred_course', 'enquiry_source')

        return Response({
            'pending_followups': list(pending_followups_calls),
            'walk_in_list': list(walk_in_list),
            'recent_calls': recent_calls_data,
            'new_enquiries': list(new_enquiries),
        })
    
class TelecallerCallSummaryView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination


    def get(self, request):
        # Only Admins can access all telecaller stats
        if not request.user.role or request.user.role.name != 'Admin':
            return Response({'error': 'Only admin can access this data.'}, status=403)

        telecallers = Telecaller.objects.all()
        response_data = []

        for telecaller in telecallers:
            calls = CallRegister.objects.filter(telecaller=telecaller)

            summary = {
                'telecaller_id': telecaller.id,
                'telecaller_name': telecaller.name,
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

        return Response({
            "code": 200,
            "message": "Telecaller call summary fetched successfully",
            "data": response_data
        })