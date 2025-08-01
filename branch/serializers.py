from rest_framework import serializers
from .models import Branch

class BranchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Branch
        fields = ['id', 'branch_name','address', 'city',  'email', 'contact']
