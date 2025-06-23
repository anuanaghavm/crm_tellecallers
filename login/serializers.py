# Serializers
from rest_framework import serializers
from .models import Account
from django.contrib.auth import authenticate
from roles.models import Role
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password']

    def create(self, validated_data):
    # Assign a default role for admin users
        role = Role.objects.get_or_create(name="Admin")[0]  # Ensure "Admin" role exists
        validated_data['role'] = role
        return User.objects.create_user(**validated_data)

class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=True)

    class Meta:
        model = Account
        fields = ['email', 'password', 'role']

    def create(self, validated_data):
        # Directly assign the password without hashing
        return Account.objects.create(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = Account.objects.get(email=data['email'], password=data['password'])  # Authenticate by plain text
        except Account.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")
        return user


class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if not Account.objects.filter(email=value).exists():
            raise serializers.ValidationError("Account with this email does not exist.")
        return value

    def update_password(self, email, new_password):
        try:
            user = Account.objects.get(email=email)
            user.password = new_password  # Update password as plain text
            user.save()
            return user
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account with this email does not exist.")

