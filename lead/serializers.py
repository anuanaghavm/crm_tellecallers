from rest_framework import serializers
from tellecaller.models import Telecaller
from .models import Lead, CallRegister
from datetime import datetime, time


class TelecallerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Telecaller
        fields = ['id', 'name', 'email']


class CallRegisterSerializer(serializers.ModelSerializer):
    call_time = serializers.DateTimeField(format="%H:%M:%S", input_formats=["%H:%M:%S", "%Y-%m-%dT%H:%M:%S"])  # accept time and full datetime

    class Meta:
        model = CallRegister
        fields = [
            'id',
            'lead',
            'call_status',
            'call_time',
            'call_date',
            'duration',
            'respond_type',
            'responds',
            'remarks',
            'created_at'
        ]
        read_only_fields = ['created_at']
class LeadSerializer(serializers.ModelSerializer):
    telecaller = TelecallerSerializer(read_only=True)
    telecaller_id = serializers.PrimaryKeyRelatedField(
        queryset=Telecaller.objects.all(),
        source='telecaller',
        write_only=True,
        required=False
    )
    calls = CallRegisterSerializer(many=True, read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'source',
            'status',
            'follow_up_date',
            'follow_up_remarks',
            'walk_in_date',
            'walk_in_remark',
            'notes',
            'follow_up',
            'created_at',
            'telecaller',
            'telecaller_id',
            'calls',
        ]
        read_only_fields = ['created_at']
