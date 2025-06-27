from rest_framework import serializers
from .models import Telecaller
from login.models import Account

class TelecallerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Accept during POST
    password_display = serializers.SerializerMethodField(read_only=True)  # Show in GET if needed
    created_by = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()

    class Meta:
        model = Telecaller
        fields = [
            'id', 'account', 'email', 'name', 'contact', 'address',
            'branch', 'branch_name', 'role', 'status',
            'created_date', 'created_by', 'password', 'password_display'
        ]
        read_only_fields = ['id', 'created_date', 'account', 'created_by', 'password_display']

    def get_created_by(self, obj):
        if obj.created_by:
            return obj.created_by.role.name
        return None

    def get_branch_name(self, obj):
        return obj.branch.branch_name if obj.branch else None

    def get_password_display(self, obj):
        # return raw_password only if you stored it
        return obj.account.raw_password if obj.account else None

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.get('email')
        role = validated_data.get('role')

        # create account first
        account = Account.objects.create(
            email=email,
            password=password,
            role=role,
            raw_password=password  # Optional: only if you store raw password
        )
        validated_data['account'] = account
        return Telecaller.objects.create(**validated_data)
