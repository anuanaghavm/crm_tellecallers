from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from .models import Branch
from .serializers import BranchSerializer
from rest_framework.response import Response
from users.models import User  
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

class BranchListCreateView(ListCreateAPIView):
    """
    Handles listing all branches and creating a new branch.
    """
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer  # Specify the serializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        """
        Add extra context to the serializer for including users if required.
        """
        context = super().get_serializer_context()
        context['include_users'] = True  # Include users in the response
        return context

def perform_create(self, serializer):
    """
    Override to handle additional logic during branch creation.
    """
    branch = serializer.save()  # Save the branch instance

    # Assign branch only to users that were pre-linked by their branch ID
    users = User.objects.filter(branch_id=branch.id)  # Filter users with the current branch ID
    for user in users:
        user.branch = branch
        user.save()  # Save the updated user with the branch assigned

class BranchRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, and deleting a branch.
    """
    queryset = Branch.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return BranchSerializer

class BranchPagination(PageNumberPagination):
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

class BranchListView(APIView):
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


        # Initial queryset (no filter by user)
        branches = Branch.objects.all().order_by('-id')

        # Optional search filter
        if search_query:
            branches = branches.filter(branch_name__istartswith=search_query)

        # Apply pagination
        paginator = BranchPagination()
        paginated_branches = paginator.paginate_queryset(branches, request)

        serializer = BranchSerializer(
            paginated_branches,
            many=True,
            context={'request': request, 'include_users': True}
        )
        return paginator.get_paginated_response(serializer.data)


class BranchTotalCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_count = Branch.objects.count()

        return Response({
            "code": 200,
            "message": "",
            "data":{
            "total_Branches": total_count,
            }
        })