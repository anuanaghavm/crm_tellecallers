from rest_framework import serializers
from .models import Enquiry
from branch.models import Branch
from login.models import Account
from tellecaller.models import Telecaller
from tellecaller.serializers import TelecallerSerializer

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'branch_name']

class EnquirySerializer(serializers.ModelSerializer):
    branch = BranchSerializer(read_only=True)
    telecaller = TelecallerSerializer(read_only=True)

    telecaller_id = serializers.PrimaryKeyRelatedField(
        queryset=Telecaller.objects.all(), source='telecaller', write_only=True
    )
    branch_id = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), source='branch', write_only=True
    )
    created_by_role = serializers.SerializerMethodField()

    def get_created_by_role(self, obj):
        return obj.created_by.role.name if obj.created_by and obj.created_by.role else None

    class Meta:
        model = Enquiry
        fields = [
            'id',
            'candidate_name',
            'phone',
            'phone2',
            'email',
            'enquiry_source',
            'branch',
            'branch_id',
            'telecaller',
            'telecaller_id',
            'preferred_course',
            'required_service',
            'feedback',
            'follow_up_on',
            'enquiry_status',
            'created_at',
            'created_by_role',
        ]
