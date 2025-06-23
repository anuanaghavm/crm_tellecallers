from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Account
from .serializers import RegisterSerializer, LoginSerializer,ChangePasswordSerializer,AdminUserSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
from users.models import User
from users.serializers import UserSerializer

class CreateAdminUserView(APIView):
    def post(self, request):
        serializer = AdminUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Admin created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class IsAdmin(BasePermission):
    """
    Custom permission to only allow access to Admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role.name == 'Admin'


class IsUser(BasePermission):
    """
    Custom permission to only allow access to User users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role.name == 'User'


class IsBranchManager(BasePermission):
    """
    Custom permission to only allow access to Branch Manager users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role.name == 'Branch Manager'

class IsAdminOrBranchManager(BasePermission):
    """
    Custom permission to allow only Admin or Branch Manager users.
    """
    def has_permission(self, request, view):
        user = request.user
        # Check if the user is authenticated and their role is either 'Admin' or 'Branch Manager'
        return (
            user.is_authenticated and 
            (user.role.name == 'Admin' or user.role.name == 'Branch Manager')
        )

class RegisterView(APIView):

    def post(self, request):
        data = request.data.copy()
        current_user = request.user

        if hasattr(current_user, "account"):  # Check if the logged-in user has an account
            data["created_by"] = current_user.account.id

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # Fetch the user's login ID (from the Login table)
            login_id = user.id  # Assuming `user.id` is the login table ID

            # Prepare user details based on their role
            role = user.role.name

            if role == 'Admin':
                # Admin does not need extra user details from User model
                return Response({
                    "login_id": login_id,
                    "role": role,
                    "refresh": str(refresh),
                    "access": access_token,
                }, status=status.HTTP_200_OK)

            # For other roles like User and Branch Manager
            try:
                user_details = User.objects.get(email=user.email)
                user_serializer = UserSerializer(user_details)

                # Ensure the login_id in the user matches the root login_id
                user_data = user_serializer.data
                user_data['login_id'] = login_id

                return Response({
                    "login_id": login_id,  # Root login ID
                    "role": role,
                    "user": user_data,  # Include updated user details
                    "refresh": str(refresh),
                    "access": access_token,
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response(
                    {"error": "No user details found for this account."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']
            serializer.update_password(email, new_password)
            return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)