from rest_framework import serializers
from .models import Telecaller
from branch.models import Branch
from login.models import Account
from django.contrib.auth.hashers import make_password

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

class TelecallerSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False)
    branch_name = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Telecaller
        fields = [
            'id', 'account', 'email', 'name', 'contact', 'address', 'role', 'branch', 'branch_name',
            'job_type', 'status', 'created_date', 'created_by', 'target',
            'password', 'username'  # for Account
        ]
        read_only_fields = ['account', 'created_date']

    def get_branch_name(self, obj):
        return obj.branch.branch_name if obj.branch else None

    def create(self, validated_data):
        password = validated_data.pop('password')
        username = validated_data.pop('username')
        email = validated_data.get('email')

        # Create Account
        account = Account.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            role=validated_data['role']  # or validated_data.pop('role')
        )

        validated_data['account'] = account
        return Telecaller.objects.create(**validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.created_by:
            representation["created_by"] = {
                "id": instance.created_by.id,
                "email": instance.created_by.email,
            }
        return representation
