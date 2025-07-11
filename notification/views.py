from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import timedelta
from django.utils import timezone
from callregister.models import CallRegister
from tellecaller.models import Telecaller
from rest_framework.pagination import PageNumberPagination 
from django.db.models import OuterRef, Subquery
from callregister.serializers import CallRegisterSerializer
from callregister.models import CallRegister
from lead.serializers import Enquiry
from lead.serializers import EnquirySerializer
from rest_framework import generics,status
from rest_framework.generics import ListAPIView


class NotificationPagination(PageNumberPagination):
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

class TelecallerRemindersView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        in_2_days = today + timedelta(days=2)
        search = request.GET.get("search", "").lower()

        def format_reminder(entry, message):
            return {
                "id": entry.id,
                "enquiry_name": entry.enquiry.candidate_name,
                "reminder_message": message,
                "created_at": entry.created_at,
                "enquiry_id": entry.enquiry.id
            }

        if user.role.name == "Admin":
            today_qs = CallRegister.objects.filter(call_outcome='Follow Up', follow_up_date=today)
            tomorrow_qs = CallRegister.objects.filter(call_outcome='Follow Up', follow_up_date=tomorrow)
            in_2_days_qs = CallRegister.objects.filter(call_outcome='Follow Up', follow_up_date=in_2_days)
            walkin_qs = CallRegister.objects.filter(call_outcome='walk_in_list')
        else:
            try:
                telecaller = Telecaller.objects.get(account=user)
            except Telecaller.DoesNotExist:
                return Response({"error": "Only telecallers and admins can access this data."}, status=403)

            today_qs = CallRegister.objects.filter(telecaller=telecaller, call_outcome='Follow Up', follow_up_date=today)
            tomorrow_qs = CallRegister.objects.filter(telecaller=telecaller, call_outcome='Follow Up', follow_up_date=tomorrow)
            in_2_days_qs = CallRegister.objects.filter(telecaller=telecaller, call_outcome='Follow Up', follow_up_date=in_2_days)
            walkin_qs = CallRegister.objects.filter(telecaller=telecaller, call_outcome='walk_in_list')

        reminders = []

        for entry in today_qs:
            reminders.append(format_reminder(entry, "Follow-up needed"))
        for entry in tomorrow_qs:
            reminders.append(format_reminder(entry, "Follow-up needed"))
        for entry in in_2_days_qs:
            reminders.append(format_reminder(entry, "Follow-up needed"))
        for entry in walkin_qs:
            reminders.append(format_reminder(entry, "Walk-in scheduled"))

        # Apply search filter
        if search:
            reminders = [
                r for r in reminders
                if search in r["enquiry_name"].lower()
            ]

        # Apply pagination
        paginator = NotificationPagination()
        paginated_reminders = paginator.paginate_queryset(reminders, request, view=self)

        return paginator.get_paginated_response(paginated_reminders)

class TelecallerDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_latest_calls_per_enquiry(self, telecaller):
        """
        Returns the latest call per enquiry for the given telecaller using Subquery.
        Compatible across all DBs.
        """
        latest_call_subquery = CallRegister.objects.filter(
            enquiry=OuterRef('enquiry'),
            telecaller=telecaller
        ).order_by('-call_start_time', '-created_at')

        return CallRegister.objects.filter(
            id__in=Subquery(latest_call_subquery.values('id')[:1])
        )

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

        # For Telecaller
        try:
            telecaller = Telecaller.objects.get(account=user)
        except Telecaller.DoesNotExist:
            return Response(
                {'error': 'Only telecallers can access dashboard.'},
                status=status.HTTP_403_FORBIDDEN
            )

        latest_calls = self.get_latest_calls_per_enquiry(telecaller)

        return Response({
            'dashboard_type': 'telecaller',
            'total_calls': CallRegister.objects.filter(telecaller=telecaller).count(),  # All calls
            'total_leads': Enquiry.objects.filter(assigned_by=telecaller).count(),
            'total_followups': latest_calls.filter(call_outcome='Follow Up').count(),
            'walkin_list': latest_calls.filter(call_outcome='walk_in_list').count(),
        })
    
class TelecallerCallSummaryView(ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination
    serializer_class = CallRegisterSerializer

    def get_latest_calls_per_enquiry(self, telecaller):
        latest_call_subquery = CallRegister.objects.filter(
            enquiry=OuterRef('enquiry'),
            telecaller=telecaller
        ).order_by('-call_start_time', '-created_at')

        return CallRegister.objects.filter(
            id__in=Subquery(latest_call_subquery.values('id')[:1])
        )

    def get_queryset(self):
        user = self.request.user
        if not user.role or user.role.name != 'Admin':
            return CallRegister.objects.none()

        report_type = self.request.query_params.get("report", "").lower()
        telecaller_id = self.request.query_params.get("telecaller_id")

        if report_type and telecaller_id:
            try:
                telecaller = Telecaller.objects.get(id=telecaller_id)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()

            latest_calls = self.get_latest_calls_per_enquiry(telecaller)

            if report_type == "contacted":
                return latest_calls.filter(call_status='contacted')
            elif report_type == "not_contacted":
                return latest_calls.filter(call_status='not_contacted')
            elif report_type == "answered":
                return latest_calls.filter(call_status='answered')
            elif report_type == "not_answered":
                return latest_calls.filter(call_status='Not Answered')
            elif report_type == "followup":
                return latest_calls.filter(call_outcome='Follow Up')
            elif report_type == "walk_in_list":
                return latest_calls.filter(call_outcome='walk_in_list')
            elif report_type == "positive":
                return latest_calls.filter(call_outcome__in=['Interested', 'Converted'])
            elif report_type == "negative":
                return latest_calls.filter(call_outcome__in=['Not Interested', 'Do Not Call'])
            else:
                return CallRegister.objects.none()

        return CallRegister.objects.none()

    def list(self, request, *args, **kwargs):
        report_type = self.request.query_params.get("report", "").lower()
        telecaller_id = self.request.query_params.get("telecaller_id")

        if report_type and telecaller_id:
            return super().list(request, *args, **kwargs)

        if not request.user.role or request.user.role.name != 'Admin':
            return Response({'error': 'Only admin can access this data.'}, status=403)

        queryset = Telecaller.objects.select_related('branch').all()

        # Optional filters
        branch_name = self.request.query_params.get('branch_name', '').strip()
        telecaller_name = self.request.query_params.get('telecaller_name', '').strip()
        search = self.request.query_params.get('search', '').strip()

        if branch_name:
            queryset = queryset.filter(branch__branch_name__icontains=branch_name)
        if telecaller_name:
            queryset = queryset.filter(name__icontains=telecaller_name)
        if search:
            queryset = queryset.filter(name__icontains=search)

        queryset = self.paginate_queryset(queryset)
        response_data = []

        for telecaller in queryset:
            all_calls = CallRegister.objects.filter(telecaller=telecaller)
            latest_calls = self.get_latest_calls_per_enquiry(telecaller)

            summary = {
                "telecaller_id": telecaller.id,
                "telecaller_name": telecaller.name,
                "branch_name": telecaller.branch.branch_name if telecaller.branch else None,
                "total_calls": all_calls.count(),  # Includes all calls
                "total_follow_ups": latest_calls.filter(call_outcome='Follow Up').count(),
                "contacted": latest_calls.filter(call_status='contacted').count(),
                "not_contacted": latest_calls.filter(call_status='not_contacted').count(),
                "answered": latest_calls.filter(call_status='answered').count(),
                "not_answered": latest_calls.filter(call_status='Not Answered').count(),
                "walk_in_list": latest_calls.filter(call_outcome='walk_in_list').count(),
                "won": latest_calls.filter(call_outcome='won').count(),
                "not_intrested": latest_calls.filter(call_outcome__in=['Not Interested', 'Do Not Call']).count(),
            }

            response_data.append(summary)

        return self.get_paginated_response(response_data)