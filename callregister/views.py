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
from datetime import datetime
from rest_framework.views import APIView
from django.db.models import Q  
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

    search_fields = [
        'enquiry__candidate_name',
        'enquiry__phone',
        'enquiry__email',
        'notes',
        'call_status',
    ]
    ordering_fields = ['call_start_time', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        query_params = self.request.query_params
        filters = Q()

        # 🔐 Restrict to current telecaller if not admin
        if user.role and user.role.name != 'Admin':
            try:
                telecaller = Telecaller.objects.get(account=user)
                filters &= Q(telecaller=telecaller)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()

        # 🔍 Query params
        candidate_name  = query_params.get('candidate_name', '').strip()
        telecaller_name = query_params.get('telecaller_name', '').strip()
        branch_name     = query_params.get('branch_name', '').strip()
        call_status     = query_params.get('call_status', '').strip()
        start_date      = query_params.get('start_date', '').strip()
        end_date        = query_params.get('end_date', '').strip()

        # 🗓️ Date filtering (created_at)
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                filters &= Q(created_at__date__gte=start)
            except ValueError:
                raise ValidationError({"error": "Invalid start_date format. Use YYYY-MM-DD."})

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                filters &= Q(created_at__date__lte=end)
            except ValueError:
                raise ValidationError({"error": "Invalid end_date format. Use YYYY-MM-DD."})

        # 📌 Outcome filter
        if call_status:
            filters &= Q(call_outcome__iexact=call_status)
        else:
            filters &= Q(call_outcome='Follow Up')

        if candidate_name:
            filters &= Q(enquiry__candidate_name__icontains=candidate_name)

        if telecaller_name:
            filters &= Q(telecaller__name__icontains=telecaller_name)

        if branch_name:
            filters &= Q(telecaller__branch__name__icontains=branch_name)

        return CallRegister.objects.select_related(
            'enquiry', 'telecaller', 'telecaller__branch'
        ).filter(filters)
# ✅ Walk-in List View with Pagination
class WalkInListView(generics.ListAPIView):
    serializer_class = CallRegisterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    search_fields = ['enquiry__candidate_name', 'enquiry__phone', 'enquiry__email']
    ordering_fields = ['call_start_time', 'created_at']
    ordering = ['-created_at']  # Default ordering

    def get_queryset(self):
        user = self.request.user
        query_params = self.request.query_params

        filters = Q(call_outcome='walk_in_list')

        if user.role and user.role.name != 'Admin':
            try:
                telecaller = Telecaller.objects.get(account=user)
                filters &= Q(telecaller=telecaller)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()

        # 🧠 Optional filters
        branch_name     = query_params.get('branch_name', '').strip()
        telecaller_name = query_params.get('telecaller_name', '').strip()
        enquiry_date    = query_params.get('enquiry_date', '').strip()
        enquiry_status  = query_params.get('enquiry_status', '').strip()
        call_status     = query_params.get('call_status', '').strip()
        start_date      = query_params.get('start_date', '').strip()
        end_date        = query_params.get('end_date', '').strip()

        if branch_name:
            filters &= Q(telecaller__branch__branch_name__icontains=branch_name)

        if telecaller_name:
            filters &= Q(telecaller__name__icontains=telecaller_name)

        if enquiry_date:
            try:
                date_obj = datetime.strptime(enquiry_date, '%Y-%m-%d').date()
                filters &= Q(enquiry__created_at__date=date_obj)
            except ValueError:
                pass

        if enquiry_status:
            filters &= Q(enquiry__enquiry_status__iexact=enquiry_status)

        if call_status:
            filters &= Q(call_status__iexact=call_status)

        # 🗓️ Date range filtering (based on `created_at`)
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                filters &= Q(created_at__date__gte=start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                filters &= Q(created_at__date__lte=end)
            except ValueError:
                pass

        return CallRegister.objects.select_related(
            'enquiry', 'telecaller', 'telecaller__branch'
        ).filter(filters)
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

        # ✅ Total calls made by this telecaller
        total_calls = CallRegister.objects.filter(telecaller=telecaller).count()

        # ✅ Enquiries assigned to this telecaller
        total_leads = Enquiry.objects.filter(assigned_by=telecaller).count()

        # ✅ All follow-up calls regardless of date
        total_followups = CallRegister.objects.filter(
            telecaller=telecaller,
            call_outcome='Follow Up'
        ).count()

        # ✅ All walk-in list calls regardless of date
        walkin_count = CallRegister.objects.filter(
            telecaller=telecaller,
            call_outcome='walk_in_list'
        ).count()

        return Response({
            'dashboard_type': 'telecaller',
            'total_calls': total_calls,
            'total_leads': total_leads,
            'total_followups': total_followups,
            'walkin_list': walkin_count,
        })
    
class TelecallerCallSummaryView(ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination

    def get_queryset(self):
        if not self.request.user.role or self.request.user.role.name != 'Admin':
            return Telecaller.objects.none()

        branch_name = self.request.query_params.get('branch_name', '').strip()
        telecaller_name = self.request.query_params.get('telecaller_name', '').strip()
        search = self.request.query_params.get('search', '').strip()  # <- use 'search'

        telecallers = Telecaller.objects.select_related('branch').all()

        if branch_name:
            telecallers = telecallers.filter(branch__branch_name__icontains=branch_name)

        if telecaller_name:
            telecallers = telecallers.filter(name__icontains=telecaller_name)

        if search:
            telecallers = telecallers.filter(name__icontains=search)  # case-insensitive partial match

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

        # Filters
        filter_status = request.query_params.get("status", "").lower()
        branch_name_filter = request.query_params.get("branch_name", "").strip().lower()
        telecaller_name_filter = request.query_params.get("telecaller_name", "").strip().lower()

        enquiries = Enquiry.objects.select_related('assigned_by__branch').order_by('-created_at')
        grouped_data = defaultdict(list)

        for enquiry in enquiries:
            telecaller = enquiry.assigned_by
            if not telecaller:
                continue

            branch_name = telecaller.branch.branch_name.lower() if telecaller.branch else ""

            # Apply filters
            if telecaller_name_filter and telecaller.name.lower() != telecaller_name_filter:
                continue
            if branch_name_filter and branch_name != branch_name_filter:
                continue

            assigned_date = enquiry.created_at.date()
            key = (telecaller.id, assigned_date, telecaller.name, branch_name)

            call = CallRegister.objects.filter(enquiry=enquiry).first()
            has_outcome = call and call.call_outcome and call.call_outcome.strip() != ""

            grouped_data[key].append(has_outcome)

        final_data = []
        for (telecaller_id, assigned_date, telecaller_name, branch_name), outcomes in grouped_data.items():
            total_jobs = len(outcomes)
            completed_jobs = sum(1 for status in outcomes if status)
            progress = f"{completed_jobs}/{total_jobs}"
            status = "Completed" if completed_jobs == total_jobs else "Remaining"

            # Filter by status
            if filter_status == "completed" and status != "Completed":
                continue
            if filter_status == "remining" and status != "Remaining":
                continue

            final_data.append({
                "telecaller_id": telecaller_id,
                "telecaller_name": telecaller_name,
                "branch_name": branch_name,
                "assigned_date": str(assigned_date),
                "progress": progress,
                "status": status
            })

        # Sort and paginate
        final_data.sort(key=lambda x: x["assigned_date"], reverse=True)
        page = self.paginate_queryset(final_data)
        if page is not None:
            return self.get_paginated_response(page)

        return Response({
            "code": 200,
            "message": "Data fetched successfully",
            "data": final_data
        })
    

class TelecallerJobsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination

    def get(self, request):
        user = request.user
        try:
            telecaller = Telecaller.objects.get(account=user)
        except Telecaller.DoesNotExist:
            return Response({"error": "Only telecallers can access this."}, status=403)

        filter_status = request.query_params.get('status', "").lower()
        name_filter = request.query_params.get("name", "").strip().lower()

        all_leads = Enquiry.objects.filter(assigned_by=telecaller).order_by('-created_at')

        result = []

        for lead in all_leads:
            if name_filter and name_filter not in lead.candidate_name.lower():
                continue

            assigned_date = lead.created_at.date()
            call = CallRegister.objects.filter(enquiry=lead).first()

            # ✅ Make sure this returns only True/False
            has_outcome = bool(call and call.call_outcome and call.call_outcome.strip())

            # ✅ Correct status filtering
            if filter_status == "completed" and not has_outcome:
                continue
            if filter_status == "remining" and has_outcome:
                continue

            result.append({
                "enquiry_id": lead.id,
                "name": lead.candidate_name,
                "contact": lead.phone,
                "email": lead.email,
                "status": "Completed" if has_outcome else "Remaining",
                "outcome": call.call_outcome if call else None,
                "telecaller_name": telecaller.name,
                "assigned_date": str(assigned_date),
            })

        result.sort(key=lambda x: x["assigned_date"], reverse=True)

        page = self.paginate_queryset(result)
        if page is not None:
            return self.get_paginated_response(page)

        return Response({
            "code": 200,
            "message": "Data fetched successfully",
            "data": result
        })


class NotAnsweredCallsView(generics.ListAPIView):
    serializer_class = CallRegisterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    search_fields = [
        'enquiry__candidate_name',
        'enquiry__phone',
        'enquiry__email',
        'notes',
        'call_status',
    ]
    ordering_fields = ['call_start_time', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        query_params = self.request.query_params

        filters = Q(call_status__iexact='Not Answered')

        if user.role and user.role.name != 'Admin':
            try:
                telecaller = Telecaller.objects.get(account=user)
                filters &= Q(telecaller=telecaller)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()

        # Query parameters
        call_status      = query_params.get('call_status', '').strip()
        telecaller_name  = query_params.get('telecaller_name', '').strip()
        enquiry_email    = query_params.get('email', '').strip()
        enquiry_phone    = query_params.get('phone', '').strip()
        candidate_name   = query_params.get('candidate_name', '').strip()
        enquiry_status   = query_params.get('enquiry_status', '').strip()
        enquiry_date     = query_params.get('enquiry_date', '').strip()

        # ✅ Date range filters
        start_date = query_params.get('start_date', '').strip()
        end_date   = query_params.get('end_date', '').strip()

        if call_status:
            filters &= Q(call_status__iexact=call_status)

        if telecaller_name:
            filters &= Q(telecaller__name__icontains=telecaller_name)

        if enquiry_email:
            filters &= Q(enquiry__email__icontains=enquiry_email)

        if enquiry_phone:
            filters &= Q(enquiry__phone__icontains=enquiry_phone)

        if candidate_name:
            filters &= Q(enquiry__candidate_name__icontains=candidate_name)

        if enquiry_status:
            filters &= Q(enquiry__enquiry_status__iexact=enquiry_status)

        if enquiry_date:
            try:
                date_obj = datetime.strptime(enquiry_date, '%Y-%m-%d').date()
                filters &= Q(enquiry__created_at__date=date_obj)
            except ValueError:
                pass

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                filters &= Q(created_at__date__gte=start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                filters &= Q(created_at__date__lte=end)
            except ValueError:
                pass

        return CallRegister.objects.select_related(
            'enquiry', 'telecaller', 'telecaller__branch'
        ).filter(filters)
    
class EnquiryCallHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, enquiry_id):
        try:
            enquiry = Enquiry.objects.get(id=enquiry_id)
        except Enquiry.DoesNotExist:
            return Response({"error": "Enquiry not found."}, status=404)

        calls = CallRegister.objects.filter(enquiry=enquiry).select_related('telecaller').order_by('-call_start_time')

        call_data = []
        for call in calls:
            call_data.append({
                "telecaller": call.telecaller.name if call.telecaller else None,
                "call_status": call.call_status,
                "call_type": call.call_type,
                "call_outcome": call.call_outcome,
                "call_start_time": call.call_start_time,
                "call_duration": call.call_duration,
                "follow_up_date": call.follow_up_date,  # ✅ Added field
                "notes": call.notes,
            })

        return Response({
            "enquiry_id": enquiry_id,
            "candidate_name": enquiry.candidate_name,
            "call_history": call_data,
        })



class InterestedCallsView(generics.ListAPIView):
    serializer_class = CallRegisterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = callsPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]

    ordering_fields = ['call_start_time', 'created_at', 'follow_up_date']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        query_params = self.request.query_params
        filters = Q(call_outcome__iexact='Interested')

        if user.role and user.role.name != 'Admin':
            try:
                telecaller = Telecaller.objects.get(account=user)
                filters &= Q(telecaller=telecaller)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()

        # ✅ Field filters
        candidate_name = query_params.get('candidate_name', '').strip()
        branch_name = query_params.get('branch_name', '').strip()
        telecaller_name = query_params.get('telecaller_name', '').strip()
        call_status = query_params.get('call_status', '').strip()
        follow_up_date = query_params.get('follow_up_date', '').strip()

        phone_number = query_params.get('phone_number', '').strip()
        email = query_params.get('email', '').strip()

        # ✅ Date filters
        start_date = query_params.get('start_date', '').strip()
        end_date = query_params.get('end_date', '').strip()

        if candidate_name:
            filters &= Q(enquiry__candidate_name__icontains=candidate_name)

        if branch_name:
            filters &= Q(telecaller__branch__branch_name__icontains=branch_name)

        if telecaller_name:
            filters &= Q(telecaller__name__icontains=telecaller_name)

        if call_status:
            filters &= Q(call_status__iexact=call_status)

        if follow_up_date:
            try:
                follow_up_obj = datetime.strptime(follow_up_date, '%Y-%m-%d').date()
                filters &= Q(follow_up_date=follow_up_obj)
            except ValueError:
                pass

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                filters &= Q(created_at__date__gte=start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                filters &= Q(created_at__date__lte=end)
            except ValueError:
                pass

        # ✅ Search by phone_number and email (related to enquiry)
        if phone_number:
            filters &= Q(enquiry__phone__icontains=phone_number)

        if email:
            filters &= Q(enquiry__email__icontains=email)

        return CallRegister.objects.select_related(
            'enquiry', 'telecaller', 'telecaller__branch'
        ).filter(filters)
