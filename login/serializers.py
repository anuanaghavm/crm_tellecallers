# login/serializers.py
from rest_framework import serializers
from .models import Account
from roles.models import Role

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Account
        fields = ['email', 'password', 'role']

    def create(self, validated_data):
        return Account.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role']
        )
