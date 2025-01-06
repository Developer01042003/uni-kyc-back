from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from .models import Company, CompanyUser
from .serializers import (CompanySerializer, CompanySignupSerializer,
                        CompanyLoginSerializer, CompanyUserSerializer)
from users.models import User

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    @action(detail=False, methods=['post'])
    def signup(self, request):
        serializer = CompanySignupSerializer(data=request.data)
        if serializer.is_valid():
            company = serializer.save()
            return Response({
                'message': 'Company registered successfully. Please wait for admin verification.',
                'company': CompanySerializer(company).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = CompanyLoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                company = Company.objects.get(email=serializer.validated_data['email'])
                if check_password(serializer.validated_data['password'], company.password):
                    refresh = RefreshToken.for_user(company)
                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'company': CompanySerializer(company).data
                    })
                return Response({'error': 'Invalid credentials'}, 
                              status=status.HTTP_401_UNAUTHORIZED)
            except Company.DoesNotExist:
                return Response({'error': 'Company not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def check_user(self, request):
        # Get API credentials from request
        api_key = request.data.get('api_key')
        api_id = request.data.get('api_id')
        user_unique_id = request.data.get('user_unique_id')

        # Validate API credentials
        try:
            company = Company.objects.get(api_key=api_key, api_id=api_id)
            
            # Check if company is verified
            if not company.is_verified:
                return Response({
                    'error': 'Company is not verified',
                    'status': False
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Check if user exists and is verified
            try:
                user = User.objects.get(unique_id=user_unique_id)
                
                if not user.is_verified:
                    return Response({
                        'error': 'User is not verified',
                        'status': False
                    }, status=status.HTTP_401_UNAUTHORIZED)

                # Check if user is already linked to the company
                existing_link = CompanyUser.objects.filter(
                    company=company,
                    user=user
                ).exists()

                if existing_link:
                    return Response({
                        'message': 'User is already linked to this company',
                        'status': 'duplicate'
                    }, status=status.HTTP_200_OK)

                return Response({
                    'message': 'User can be added to the company',
                    'status': True
                }, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({
                    'error': 'User not found',
                    'status': False
                }, status=status.HTTP_404_NOT_FOUND)

        except Company.DoesNotExist:
            return Response({
                'error': 'Invalid API credentials',
                'status': False
            }, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def add_user(self, request):
        # Get API credentials from request
        api_key = request.data.get('api_key')
        api_id = request.data.get('api_id')
        user_unique_id = request.data.get('user_unique_id')

        # Validate API credentials
        try:
            company = Company.objects.get(api_key=api_key, api_id=api_id)
            
            # Check if company is verified
            if not company.is_verified:
                return Response({
                    'error': 'Company is not verified'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Check if user exists and is verified
            try:
                user = User.objects.get(unique_id=user_unique_id)
                
                if not user.is_verified:
                    return Response({
                        'error': 'User is not verified'
                    }, status=status.HTTP_401_UNAUTHORIZED)

                # Check if user is already linked to the company
                existing_link = CompanyUser.objects.filter(
                    company=company,
                    user=user
                ).exists()

                if existing_link:
                    return Response({
                        'error': 'User is already linked to this company'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Create new company-user link
                company_user = CompanyUser.objects.create(
                    company=company,
                    user=user
                )

                return Response({
                    'message': 'User successfully added to company',
                    'data': CompanyUserSerializer(company_user).data
                }, status=status.HTTP_201_CREATED)

            except User.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)

        except Company.DoesNotExist:
            return Response({
                'error': 'Invalid API credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)