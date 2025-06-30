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

        if not user.check_password(data['password']):
            raise serializers.ValidationError("Invalid credentials")

        return user

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField()

    def validate(self, data):
        try:
            user = Account.objects.get(email=data['email'])
        except Account.DoesNotExist:
            raise serializers.ValidationError("Email not registered")

        return data

    def save(self):
        email = self.validated_data['email']
        new_password = self.validated_data['new_password']
        user = Account.objects.get(email=email)
        user.set_password(new_password)
        user.raw_password = new_password
        user.save()
        return user
