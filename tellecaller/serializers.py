from rest_framework import serializers
from .models import Telecaller
from login.models import Account

class TelecallerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  
    password_display = serializers.SerializerMethodField(read_only=True)  
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
        return obj.account.raw_password if obj.account else None

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.get('email')
        role = validated_data.get('role')
        account = Account(
            email=email,
            role=role,
            raw_password=password  
        )
        account.set_password(password)
        account.save()
        validated_data['account'] = account
        validated_data['email'] = account.email
        return Telecaller.objects.create(**validated_data)

    def update(self, instance, validated_data):
        account = instance.account

        email = validated_data.pop('email', None)
        password = validated_data.pop('password', None)
        if email:
            account.email = email
            instance.email = email  
        if password:
            account.set_password(password)
            account.raw_password = password

        account.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
