from rest_framework import serializers
from .models import Company, CompanyUser
from users.models import User
from users.serializers import UserSerializer

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'email', 'address', 'country', 'is_verified', 
                 'is_kyc_need', 'is_unique', 'api_id', 'api_key', 'created_at', 'updated_at']
        read_only_fields = ['api_id', 'api_key']

class CompanySignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['name', 'email', 'password', 'address', 'country']
        extra_kwargs = {'password': {'write_only': True}}

class CompanyLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class CompanyUserSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    company = CompanySerializer()

    class Meta:
        model = CompanyUser
        fields = ['id', 'company', 'user', 'created_at']