from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import timedelta
from django.utils import timezone
from callregister.models import CallRegister
from tellecaller.models import Telecaller
from rest_framework.pagination import PageNumberPagination 

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

