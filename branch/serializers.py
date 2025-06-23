from rest_framework import serializers
from .models import Branch
from users.models import User  # Adjust the import path for the User model

class UserForBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class BranchSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = ['id', 'branch_name', 'branch_code', 'address', 'city', 'state', 'country', 'email', 'contact', 'users']

    def get_users(self, obj):
        # Check if 'include_users' is passed in the request context
        if self.context.get('include_users', False):
            users = User.objects.filter(branch=obj)
            return UserForBranchSerializer(users, many=True).data
        return None
