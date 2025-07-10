from rest_framework import serializers
from .models import Enquiry
from branch.models import Branch
from login.models import Account
from tellecaller.models import Telecaller
from tellecaller.serializers import TelecallerSerializer
from rest_framework import serializers
from .models import CallRegister
from lead.models import Enquiry
from tellecaller.models import Telecaller
from django.utils import timezone


class CallRegisterSerializer(serializers.ModelSerializer):
    enquiry_id = serializers.PrimaryKeyRelatedField(
        queryset=Enquiry.objects.all(), source='enquiry', write_only=True
    )
    
    # Read-only fields for response
    enquiry_details = serializers.SerializerMethodField()
    telecaller_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    call_duration_formatted = serializers.SerializerMethodField()

    class Meta:
        model = CallRegister
        fields = [
            'id',
            'enquiry_id',
            'enquiry_details',
            'telecaller_name',
            'branch_name',
            'call_type',
            'call_status',
            'call_outcome',
            'call_duration',
            'call_duration_formatted',
            'call_start_time',
            'call_end_time',
            'notes',
            'follow_up_date',
            'next_action',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'call_duration']

    def get_enquiry_details(self, obj):
        return {
            'id': obj.enquiry.id,
            'candidate_name': obj.enquiry.candidate_name,
            'phone': obj.enquiry.phone,
            'email': obj.enquiry.email,
            'enquiry_status': obj.enquiry.enquiry_status,
        }

    def get_telecaller_name(self, obj):
        return obj.telecaller.name

    def get_branch_name(self, obj):
        return obj.telecaller.branch.branch_name if obj.telecaller.branch else None

    def get_call_duration_formatted(self, obj):
        if obj.call_duration:
            minutes = obj.call_duration // 60
            seconds = obj.call_duration % 60
            return f"{minutes}m {seconds}s"
        return None

    def validate(self, data):
        request_user = self.context['request'].user
        
        # Get telecaller for the current user
        try:
            telecaller = Telecaller.objects.get(account=request_user)
        except Telecaller.DoesNotExist:
            raise serializers.ValidationError("Only telecallers can create call logs.")
        
        # Set the telecaller
        data['telecaller'] = telecaller
        
        # Validate enquiry assignment
        enquiry = data.get('enquiry')
        if enquiry.assigned_by != telecaller:
            raise serializers.ValidationError({
                'enquiry_id': 'You can only create call logs for enquiries assigned to you.'
            })
        
        # Validate call times
        call_start_time = data.get('call_start_time')
        call_end_time = data.get('call_end_time')
        
        if call_start_time and call_start_time > timezone.now():
            raise serializers.ValidationError({
                'call_start_time': 'Call start time cannot be in the future.'
            })
        
        if call_end_time and call_start_time and call_end_time < call_start_time:
            raise serializers.ValidationError({
                'call_end_time': 'Call end time must be after start time.'
            })
        
        # Validate follow-up date
        follow_up_date = data.get('follow_up_date')
        if follow_up_date and follow_up_date <= timezone.now().date():
            raise serializers.ValidationError({
                'follow_up_date': 'Follow-up date must be in the future.'
            })
        
        return data

    def create(self, validated_data):
        # Update enquiry status based on call outcome
        enquiry = validated_data['enquiry']
        call_outcome = validated_data.get('call_outcome')
        
        if call_outcome == 'Converted':
            enquiry.enquiry_status = 'Closed'
        elif call_outcome == 'Not Interested':
            enquiry.enquiry_status = 'Not Interested'
        elif call_outcome in ['Follow Up Required', 'Callback Requested']:
            enquiry.enquiry_status = 'Follow Up'
            if validated_data.get('follow_up_date'):
                enquiry.follow_up_on = validated_data['follow_up_date']
        
        enquiry.save()
        
        return super().create(validated_data)
