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
from django.db.models import Max
from django.utils.dateparse import parse_date

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

        # Get base queryset
        base_qs = CallRegister.objects.all()

        # Filter for telecaller if not admin
        if user.role.name != "Admin":
            try:
                telecaller = Telecaller.objects.get(account=user)
            except Telecaller.DoesNotExist:
                return Response({"error": "Only telecallers and admins can access this data."}, status=403)
            base_qs = base_qs.filter(telecaller=telecaller)

        # Get only the latest CallRegister entry per enquiry
        latest_ids = base_qs.values('enquiry').annotate(latest_id=Max('id')).values('latest_id')
        latest_calls = CallRegister.objects.filter(id__in=Subquery(latest_ids))

        # Filter latest calls by outcome and date
        filtered_qs = latest_calls.filter(
            call_outcome__in=['Follow Up', 'walk_in_list'],
            follow_up_date__in=[today, tomorrow, in_2_days]
        )

        # Format reminders
        reminders = []
        for entry in filtered_qs:
            message = "Walk-in scheduled" if entry.call_outcome == 'walk_in_list' else "Follow-up needed"
            reminders.append(format_reminder(entry, message))

        # Apply search filter
        if search:
            reminders = [r for r in reminders if search in r["enquiry_name"].lower()]

        # Apply pagination
        paginator = NotificationPagination()
        paginated_reminders = paginator.paginate_queryset(reminders, request, view=self)

        return paginator.get_paginated_response(paginated_reminders)

class TelecallerDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_enquiries_with_latest_call_status(self, telecaller):
        """
        Annotate each enquiry assigned to the telecaller with the latest call outcome
        (regardless of which telecaller made the call).
        """
        latest_call_subquery = (
            CallRegister.objects
            .filter(enquiry_id=OuterRef('pk'))
            .order_by('-created_at')  # Use '-id' if 'created_at' not available
        )

        # Only get enquiries assigned to the logged-in telecaller
        enquiries_with_latest = (
            Enquiry.objects
            .filter(assigned_by=telecaller)
            .annotate(
                latest_call_outcome=Subquery(latest_call_subquery.values('call_outcome')[:1])
            )
        )

        return enquiries_with_latest

    def get(self, request):
        user = request.user

        # Admin dashboard logic
        if user.role and user.role.name == 'Admin':
            return Response({
                'dashboard_type': 'admin',
                'total_calls': CallRegister.objects.count(),
                'total_leads': Enquiry.objects.count(),
                'total_telecallers': Telecaller.objects.count(),
            })

        # Telecaller dashboard logic
        try:
            telecaller = Telecaller.objects.get(account=user)
        except Telecaller.DoesNotExist:
            return Response({'error': 'Only telecallers can access dashboard.'}, status=403)

        # Enquiries assigned to telecaller with latest call outcome
        enquiries = self.get_enquiries_with_latest_call_status(telecaller)

        # Count based on latest call outcome
        pending_followups = enquiries.filter(latest_call_outcome='Follow Up').count()
        walkin_list = enquiries.filter(latest_call_outcome='walk_in_list').count()

        return Response({
            'dashboard_type': 'telecaller',
            'total_calls': CallRegister.objects.filter(telecaller=telecaller).count(),
            'total_leads': enquiries.count(),  # Count of active enquiries assigned
            'pending_followups': pending_followups,
            'walkin_list': walkin_list,
        })
    
class TelecallerCallSummaryView(ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination
    serializer_class = CallRegisterSerializer

    def get_latest_calls_per_enquiry(self, telecaller, start_date=None, end_date=None):
        calls_qs = CallRegister.objects.filter(telecaller=telecaller)

        # ✅ Apply date filtering ONLY if dates are given
        if start_date and end_date:
            calls_qs = calls_qs.filter(created_at__date__range=(start_date, end_date))
        elif start_date:
            calls_qs = calls_qs.filter(created_at__date__gte=start_date)
        elif end_date:
            calls_qs = calls_qs.filter(created_at__date__lte=end_date)

        # ✅ Always return latest call per enquiry from the (possibly filtered) list
        latest_calls_map = (
            calls_qs
            .values('enquiry_id')
            .annotate(latest_call_id=Max('id'))
            .values_list('latest_call_id', flat=True)
        )

        return CallRegister.objects.filter(id__in=list(latest_calls_map))

    def get_queryset(self):
        user = self.request.user
        if not user.role or user.role.name != 'Admin':
            return CallRegister.objects.none()

        report_type = self.request.query_params.get("report", "").lower()
        telecaller_id = self.request.query_params.get("telecaller_id")
        start_date = parse_date(self.request.query_params.get("start_date", ""))
        end_date = parse_date(self.request.query_params.get("end_date", ""))

        if report_type and telecaller_id:
            try:
                telecaller = Telecaller.objects.get(id=telecaller_id)
            except Telecaller.DoesNotExist:
                return CallRegister.objects.none()

            latest_calls = self.get_latest_calls_per_enquiry(telecaller, start_date, end_date)

            # Filter based on report type
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
            elif report_type == "won":
                return latest_calls.filter(call_outcome__in=['Won'])
            elif report_type == "totalcalls":
                all_calls = CallRegister.objects.filter(telecaller=telecaller)
                if start_date and end_date:
                    all_calls = all_calls.filter(created_at__date__range=(start_date, end_date))
                elif start_date:
                    all_calls = all_calls.filter(created_at__date__gte=start_date)
                elif end_date:
                    all_calls = all_calls.filter(created_at__date__lte=end_date)
                return all_calls


    def list(self, request, *args, **kwargs):
        report_type = self.request.query_params.get("report", "").lower()
        telecaller_id = self.request.query_params.get("telecaller_id")
        start_date = parse_date(self.request.query_params.get("start_date", ""))
        end_date = parse_date(self.request.query_params.get("end_date", ""))

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
            latest_calls = self.get_latest_calls_per_enquiry(telecaller, start_date, end_date)

            if not latest_calls.exists():
                continue  # ✅ Valid here — inside the loop

            # Optional: filter total_calls by date
            if start_date and end_date:
                all_calls = all_calls.filter(created_at__date__range=(start_date, end_date))
            elif start_date:
                all_calls = all_calls.filter(created_at__date__gte=start_date)
            elif end_date:
                all_calls = all_calls.filter(created_at__date__lte=end_date)

            summary = {
                "telecaller_id": telecaller.id,
                "telecaller_name": telecaller.name,
                "branch_name": telecaller.branch.branch_name if telecaller.branch else None,
                "total_calls": all_calls.count(),
                "total_follow_ups": latest_calls.filter(call_outcome='Follow Up').count(),
                "contacted": latest_calls.filter(call_status='contacted').count(),
                "not_contacted": latest_calls.filter(call_status='not_contacted').count(),
                "answered": latest_calls.filter(call_status='Answered').count(),
                "not_answered": latest_calls.filter(call_status='Not Answered').count(),
                "walk_in_list": latest_calls.filter(call_outcome='walk_in_list').count(),
                "won": latest_calls.filter(call_outcome='Won').count(),
                "not_intrested": latest_calls.filter(call_outcome__in=['Not Interested', 'Do Not Call']).count(),
            }

            response_data.append(summary)

        return self.get_paginated_response(response_data)