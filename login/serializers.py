from rest_framework import serializers
from login.models import Account
from roles.models import Role

class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    class Meta:
        model = Account
        fields = ['email', 'password', 'role']

    def create(self, validated_data):
        return Account.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = Account.objects.get(email=data['email'])
        except Account.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        if user.raw_password != data['password']:
            raise serializers.ValidationError("Invalid credentials")

        return user
