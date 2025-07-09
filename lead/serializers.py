# serializers.py
from rest_framework import serializers
from .models import Enquiry, Mettad, Course, Service
from branch.models import Branch
from login.models import Account
from tellecaller.models import Telecaller
from tellecaller.serializers import TelecallerSerializer
from django.utils import timezone

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'branch_name']

class MettadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mettad
        fields = ['id', 'name']

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'is_active', 'created_at']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'is_active', 'created_at']

# Updated EnquirySerializer with Course and Service integration
class EnquirySerializer(serializers.ModelSerializer):
    assigned_by_id = serializers.PrimaryKeyRelatedField(
        queryset=Telecaller.objects.all(), source='assigned_by', write_only=True, required=False
    )
    assigned_by_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    
    created_by_role = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    # Mettad fields
    mettad_id = serializers.PrimaryKeyRelatedField(
        queryset=Mettad.objects.all(), source='Mettad', write_only=True, required=False
    )
    mettad_name = serializers.SerializerMethodField()
    
    # Course fields
    preferred_course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), source='preferred_course', write_only=True, required=False
    )
    required_service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), source='required_service', write_only=True, required=False
    )
    preferred_course_name = serializers.SerializerMethodField()
    required_service_name = serializers.SerializerMethodField()

    class Meta:
        model = Enquiry
        fields = [
            'id',
            'candidate_name',
            'phone',
            'phone2',
            'email',
            'feedback',
            'follow_up_on',
            'enquiry_status',
            'created_at',
            
            # Role-based logic
            'created_by_role',
            'created_by_name',
            'assigned_by_id',
            'assigned_by_name',
            'branch_name',
            
            # Mettad fields
            'mettad_id',
            'mettad_name',
            
            # Course fields
            'preferred_course_id',
            'preferred_course_name',
            
            # Service fields
            'required_service_id',
            'required_service_name',
        ]

    def get_created_by_role(self, obj):
        return obj.created_by.role.name if obj.created_by and obj.created_by.role else None

    def get_created_by_name(self, obj):
        if obj.created_by:
            if obj.created_by.role.name == 'Admin':
                return "Admin"
            telecaller = Telecaller.objects.filter(account=obj.created_by).first()
            return telecaller.name if telecaller else obj.created_by.email
        return None

    def get_assigned_by_name(self, obj):
        return obj.assigned_by.name if obj.assigned_by else None

    def get_branch_name(self, obj):
        return obj.assigned_by.branch.branch_name if obj.assigned_by and obj.assigned_by.branch else None

    def get_mettad_name(self, obj):
        return obj.Mettad.name if obj.Mettad else None
    
    def get_preferred_course_name(self, obj):
        return obj.preferred_course.name if obj.preferred_course else None
    
    def get_required_service_name(self, obj):
        return obj.required_service.name if obj.required_service else None

    def validate(self, data):
        request_user = self.context['request'].user
        role = request_user.role.name if request_user.role else None

        if role == 'Admin':
            if not data.get('assigned_by'):
                raise serializers.ValidationError({
                    'assigned_by_id': 'assigned_by is required when created_by is Admin.'
                })
        else:
            # Auto-assign the same telecaller as assigned_by
            telecaller = Telecaller.objects.filter(account=request_user).first()
            if telecaller:
                data['assigned_by'] = telecaller
            else:
                raise serializers.ValidationError("Only telecallers can create enquiry without assigning manually.")

        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    



