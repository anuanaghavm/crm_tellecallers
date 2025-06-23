from rest_framework import serializers
from .models import  User
from login.models import Account
from branch.models import Branch


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'branch_name', 'branch_code', 'address', 'city', 'state', 'country', 'email', 'contact']

class UserSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False)
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False)
    branch_name = serializers.SerializerMethodField()
    password = serializers.CharField(source='account.password', required=False)

    class Meta:
        model = User
        fields = [
            "id", "account", "email", "name", "contact", "address", 
            "role", "job_type", "status", "created_date", "created_by", 
            "branch", "branch_name", "password", 'target'
        ]

    def get_branch_name(self, obj):
        return obj.branch.branch_name if obj.branch else None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.created_by:
            created_by_user = getattr(instance.created_by, "user", None)
            representation["created_by"] = {
                "id": instance.created_by.id,
                "name": "Admin" if instance.created_by.role.name == "Admin" else (
                    created_by_user.name if created_by_user else "Unknown"
                )
            }
        return representation

    def update(self, instance, validated_data):
        account_data = validated_data.pop('account', None)

        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update Account fields if present
        if account_data:
            if 'email' in account_data:
                instance.account.email = account_data['email']
            if 'password' in account_data:
                instance.account.password = account_data['password']  # Note: Stored as plain text (not secure)
            instance.account.save()

        return instance



class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'contact', 'address', 'job_type', 'status', 'created_date']
