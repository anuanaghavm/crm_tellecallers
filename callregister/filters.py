# enquiry/filters.py

import django_filters
from .models import CallRegister
from django.utils import timezone

class NotAnsweredCallsFilter(django_filters.FilterSet):
    telecaller_name = django_filters.CharFilter(field_name="telecaller__name", lookup_expr="icontains")
    branch_name = django_filters.CharFilter(field_name="telecaller__branch__branch_name", lookup_expr="icontains")
    enquiry_date = django_filters.DateFilter(field_name="enquiry__created_at__date")
    enquiry_status = django_filters.CharFilter(field_name="enquiry__enquiry_status", lookup_expr="iexact")

    class Meta:
        model = CallRegister
        fields = ['telecaller_name', 'branch_name', 'enquiry_date', 'enquiry_status']
class WalkInListFilter(django_filters.FilterSet):
    telecaller_name = django_filters.CharFilter(
        field_name="telecaller__name", lookup_expr="icontains"
    )
    branch_name = django_filters.CharFilter(
        field_name="telecaller__branch__branch_name", lookup_expr="icontains"
    )
    created_at = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date"
    )
    call_outcome = django_filters.CharFilter(
        field_name="call_outcome", lookup_expr="iexact"
    )
    call_status = django_filters.CharFilter(
        field_name="call_status", lookup_expr="iexact"
    )
    candidate_name = django_filters.CharFilter(
        field_name="enquiry__candidate_name", lookup_expr="icontains"
    )

    class Meta:
        model = CallRegister
        fields = [
            'telecaller_name',
            'branch_name',
            'created_at',
            'call_outcome',
            'call_status',
            'candidate_name',
        ]



class FollowUpCallsFilter(django_filters.FilterSet):
    telecaller_name = django_filters.CharFilter(
        field_name="telecaller__name", lookup_expr="icontains"
    )
    branch_name = django_filters.CharFilter(
        field_name="telecaller__branch__branch_name", lookup_expr="icontains"
    )
    enquiry_date = django_filters.DateFilter(
        field_name="enquiry__created_at__date"
    )
    enquiry_status = django_filters.CharFilter(
        field_name="enquiry__enquiry_status", lookup_expr="iexact"
    )
    follow_up_date = django_filters.DateFilter(
        field_name="follow_up_date"
    )
    pending_only = django_filters.BooleanFilter(
        method="filter_pending_only",
        label="Pending only (follow_up_date ≤ today)"
    )

    class Meta:
        model = CallRegister
        fields = [
            "telecaller_name",
            "branch_name",
            "enquiry_date",
            "enquiry_status",
            "follow_up_date",
            "pending_only",
        ]

    def filter_pending_only(self, queryset, name, value):
        """
        If pending_only=True, only include calls whose follow_up_date is today or earlier.
        """
        if value:
            today = timezone.now().date()
            return queryset.filter(follow_up_date__lte=today)
        return queryset
