from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import timedelta
from django.utils import timezone
from callregister.models import CallRegister
from tellecaller.models import Telecaller

class TelecallerRemindersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        in_2_days = today + timedelta(days=2)

        def format_reminder(entry, message):
            return {
                "id": entry.id,
                "enquiry_name": entry.enquiry.candidate_name,
                "reminder_message": message,
                "created_at": entry.created_at,
                "enquiry_id": entry.enquiry.id
            }

        # Admin sees all, telecaller sees own
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

        # Format all reminders
        reminders = []

        for entry in today_qs:
            reminders.append(format_reminder(entry, "Follow-up needed"))

        for entry in tomorrow_qs:
            reminders.append(format_reminder(entry, "Follow-up needed"))

        for entry in in_2_days_qs:
            reminders.append(format_reminder(entry, "Follow-up needed"))

        for entry in walkin_qs:
            reminders.append(format_reminder(entry, "Walk-in scheduled"))

        return Response({
            "code": 200,
            "message": "Reminders fetched successfully",
            "reminders": reminders
        })
