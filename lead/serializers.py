from tellecaller.models import Telecaller
from rest_framework import serializers
from .models import Lead

class TelecallerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Telecaller
        fields = ['id', 'name', 'email']

class LeadSerializer(serializers.ModelSerializer):
    telecaller = TelecallerSerializer(read_only=True)
    telecaller_id = serializers.PrimaryKeyRelatedField(
        queryset=Telecaller.objects.all(),
        source='telecaller',
        write_only=True,
        required=False
    )

    class Meta:
        model = Lead
        fields = '__all__'
