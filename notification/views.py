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

        def format_reminders(queryset):
            return [f"{entry.enquiry.candidate_name} needs followups" for entry in queryset]

        def format_walkins(queryset):
            return [f"{entry.enquiry.candidate_name} in walk-in list" for entry in queryset]

        # ✅ Check admin based on role
        if user.role.name == "Admin":
            today_qs = CallRegister.objects.filter(call_outcome='Follow Up', follow_up_date=today)
            tomorrow_qs = CallRegister.objects.filter(call_outcome='Follow Up', follow_up_date=tomorrow)
            in_2_days_qs = CallRegister.objects.filter(call_outcome='Follow Up', follow_up_date=in_2_days)
            walkin_qs = CallRegister.objects.filter(call_outcome='walk_in_list')

        else:
            # ✅ Telecaller view
            try:
                telecaller = Telecaller.objects.get(account=user)
            except Telecaller.DoesNotExist:
                return Response({"error": "Only telecallers and admins can access this data."}, status=403)

            today_qs = CallRegister.objects.filter(telecaller=telecaller, call_outcome='Follow Up', follow_up_date=today)
            tomorrow_qs = CallRegister.objects.filter(telecaller=telecaller, call_outcome='Follow Up', follow_up_date=tomorrow)
            in_2_days_qs = CallRegister.objects.filter(telecaller=telecaller, call_outcome='Follow Up', follow_up_date=in_2_days)
            walkin_qs = CallRegister.objects.filter(telecaller=telecaller, call_outcome='walk_in_list')

        # Format and return
        today_reminders = format_reminders(today_qs)
        tomorrow_reminders = format_reminders(tomorrow_qs)
        in_2_days_reminders = format_reminders(in_2_days_qs)
        walkin_reminders = format_walkins(walkin_qs)

        return Response({
            "code": 200,
            "message": "Reminders fetched successfully",
            "reminders": today_reminders + tomorrow_reminders + in_2_days_reminders + walkin_reminders
        })
