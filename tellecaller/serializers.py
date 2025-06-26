from rest_framework import serializers
from .models import Telecaller
from login.models import Account

class TelecallerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Telecaller
        fields = [
            'id', 'account', 'email', 'name', 'contact', 'address',
            'role', 'status', 'created_date', 'created_by', 'password'
        ]
        read_only_fields = ['id', 'created_date', 'account', 'created_by']

    def get_created_by(self, obj):
        if obj.created_by:
            return obj.created_by.role.name  # Return role name like 'Admin'
        return None

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.get('email')
        role = validated_data.get('role')

        account = Account.objects.create(
            email=email,
            password=password,
            role=role,
            raw_password=password
        )
        validated_data['account'] = account
        return Telecaller.objects.create(**validated_data)
