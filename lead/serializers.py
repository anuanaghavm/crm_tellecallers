from rest_framework import serializers
from .models import Enquiry, Mettad, Course, Service, checklist
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

class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = checklist
        fields = ['id', 'name']

class EnquirySerializer(serializers.ModelSerializer):
    assigned_by_id = serializers.PrimaryKeyRelatedField(
        queryset=Telecaller.objects.all(), source='assigned_by', required=False
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

    # Checklist
    checklist_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=checklist.objects.all(), source='checklist', write_only=True, required=False
    )
    checklist = ChecklistSerializer(many=True, read_only=True)

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

            # Role-related
            'created_by_role',
            'created_by_name',
            'assigned_by_id',
            'assigned_by_name',
            'branch_name',

            # Mettad
            'mettad_id',
            'mettad_name',

            # Course & Service
            'preferred_course_id',
            'preferred_course_name',
            'required_service_id',
            'required_service_name',

            # Checklist
            'checklist_ids',
            'checklist',
        ]

    def __init__(self, *args, **kwargs):
        """
        Custom __init__ to handle dynamic checklistN keys from form-data.
        Only process POST data when 'data' is provided and request method is POST.
        """
        request = kwargs.get('context', {}).get('request')
        
        # Only process form data if:
        # 1. We have a request object
        # 2. The request method is POST/PUT/PATCH (not GET)
        # 3. 'data' is provided in kwargs (indicating this is for writing, not reading)
        if (request and 
            hasattr(request, 'method') and 
            request.method in ['POST', 'PUT', 'PATCH'] and 
            'data' in kwargs and
            hasattr(request, 'POST')):
            
            data = request.POST.copy()  # make mutable

            checklist_ids = []
            for key in list(data.keys()):
                if key.startswith('checklist') and key != 'checklist_ids':
                    value = data.get(key)
                    if value and value.isdigit():
                        checklist_ids.append(int(value))

            if checklist_ids:
                data.setlist('checklist_ids', checklist_ids)

            kwargs['data'] = data

        super().__init__(*args, **kwargs)

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
            telecaller = Telecaller.objects.filter(account=request_user).first()
            if telecaller:
                data['assigned_by'] = telecaller
            else:
                raise serializers.ValidationError("Only telecallers can create enquiry without assigning manually.")
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)