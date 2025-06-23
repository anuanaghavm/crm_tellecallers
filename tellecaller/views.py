from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status,generics
from .models import User
from .serializers import UserSerializer
from login.views import IsAdmin,IsAdminOrBranchManager,IsUser
from login.serializers import RegisterSerializer
from .models import User, Role
from rest_framework.pagination import PageNumberPagination


class UserListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrBranchManager]  # Require JWT Authentication

    def get(self, request):
        # Retrieve all user instances
        users = User.objects.all()

        # Serialize the user data
        user_serializer = UserSerializer(users, many=True)

        # Format the created_date field to only show the date (no time)
        for user in user_serializer.data:
            # Format created_date as dd-mm-yyyy
            if "created_date" in user:
                user["created_date"] = user["created_date"].split("T")[0]  # Extract date part (before 'T')

        return Response({
            "users": user_serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        account_serializer = RegisterSerializer(data=request.data)
        if account_serializer.is_valid():
            # Save the account (this creates the `Account` instance)
            account = account_serializer.save()

            # Extract role from request data
            role = request.data.get("role")

            # Create the `User` instance
            user_data = {
                "account": account.id,
                "email": request.data.get("email"),
                "name": request.data.get("name"),
                "contact": request.data.get("contact"),
                "address": request.data.get("address"),
                "role": role,
                "branch": request.data.get("branch"),
                "target": request.data.get("target"),
                "job_type": request.data.get("job_type"),
                "created_by": request.user.id , # Assuming `created_by` is the logged-in user's account ID
                
            }

            user_serializer = UserSerializer(data=user_data)
            if user_serializer.is_valid():
                user = user_serializer.save()

                # Format the created_date field to only show the date (no time)
                created_date = user.created_date
                formatted_date = created_date.strftime("%d-%m-%Y")  # Format to the desired format

                # Generate a role-specific success message
                if role == "2":  # Assuming role is sent as a string
                    message = "Branch Manager created successfully"
                elif role == "3":  # Assuming role is sent as a string
                    message = "User created successfully"
                else:
                    message = "User created successfully"  # Default message for other roles

                # Return response with formatted created_date
                response_data = user_serializer.data
                response_data["created_date"] = formatted_date  # Replace with formatted date

                return Response({
                    "message": message,
                    "user_data": response_data
                }, status=status.HTTP_201_CREATED)
            else:
                account.delete()  # Cleanup the account if user creation fails
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(account_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated,IsAdminOrBranchManager]  # Require JWT Authentication

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
class UsersByRoleView(APIView):
    def get(self, request, role_id):
        try:
            # Fetch the role
            role = Role.objects.get(id=role_id)

            # Filter users by the role
            users = User.objects.filter(role=role)

            # Serialize the data
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        
class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "code": 200,
            "message": "",
            "data": data,
            "pagination": {
                "total": self.page.paginator.count,
                "page": self.page.number,
                "limit": self.get_page_size(self.request),
                "totalPages": self.page.paginator.num_pages,
            }
        })

class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search_query = request.query_params.get('search', '')
        page = request.query_params.get('page')
        limit = request.query_params.get('limit')

        if page is None or limit is None or search_query is None:
            return Response({
                "code": 200,
                "message": "",
                "data": "",
                "pagination": {
                    "total": self.page.paginator.count,
                    "page": self.page.number,
                    "limit": self.get_page_size(self.request),
                    "totalPages": self.page.paginator.num_pages,
                }
            })

        # Filter customers created by the currently authenticated user
        user = request.user

        # Show all if user is admin, otherwise show only their own
        if user.role.name == "Admin":
            users = User.objects.all().order_by('id')
        else:
            users = User.objects.filter(created_by=user)

        if search_query:
            users = users.filter(name__istartswith=search_query)

        paginator = UserPagination()
        paginated_agents = paginator.paginate_queryset(users, request)

        serializer = UserSerializer(paginated_agents, many=True)
        return paginator.get_paginated_response(serializer.data) 
    

class UsersReportsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # Authenticated user from token
        users = User.objects.filter(created_by=user)  # Filter by created_by

        if not users.exists():
            return Response({
                "code": 200,
                "message": "",
                "result": []
            }, status=status.HTTP_200_OK)

        serializer = UserSerializer(users, many=True)
        return Response({
            "code": 200,
            "message": "",
            "result": serializer.data
        }, status=status.HTTP_200_OK)
    
class UserTotalCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Admin can view total count of all customers
        if user.role.name == "Admin":
            total_users = User.objects.count()
        else:
            # Non-admin users can view only the count of their own customers
            total_users = User.objects.filter(created_by=user).count()

        return Response({
            "code": 200,
            "message": "",
            "data": {
            "total_users": total_users
            }
        }, status=200)