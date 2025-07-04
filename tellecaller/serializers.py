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
        return obj.account.raw_password if obj.account else None

    def create(self, validated_data):
        # Step 1: Extract password
        password = validated_data.pop('password')
        email = validated_data.get('email')
        role = validated_data.get('role')

        # Step 2: Create Account securely with hashed password
        account = Account(
            email=email,
            role=role,
            raw_password=password  # only if you want to store the raw version
        )
        account.set_password(password)
        account.save()

        # Step 3: Sync email with Telecaller model (required!)
        validated_data['account'] = account
        validated_data['email'] = account.email

        # Step 4: Create Telecaller
        return Telecaller.objects.create(**validated_data)

    def update(self, instance, validated_data):
        account = instance.account

        email = validated_data.pop('email', None)
        password = validated_data.pop('password', None)

        # Update email
        if email:
            account.email = email
            instance.email = email  # keep both in sync

        # Update password securely
        if password:
            account.set_password(password)
            account.raw_password = password

        account.save()

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
