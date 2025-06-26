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
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Telecaller
        fields = [
            'id', 'uuid', 'account', 'email', 'name', 'contact', 'address',
            'role', 'branch', 'status', 'created_date', 'created_by',
            'password'
        ]
        read_only_fields = ['id', 'uuid', 'account', 'created_date']


    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.get('email')

        # Create Account
        account = Account.objects.create(
            email=email,
            password=password,
            role=validated_data['role']
        )
        validated_data['account'] = account
        return Telecaller.objects.create(**validated_data)
