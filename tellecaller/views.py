from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .models import Telecaller
from .serializers import TelecallerSerializer
from roles.models import Role

class TelecallerPagination(PageNumberPagination):
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

class TelecallerListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        telecallers = Telecaller.objects.all().order_by('-id')
        paginator = TelecallerPagination()
        result_page = paginator.paginate_queryset(telecallers, request)
        serializer = TelecallerSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TelecallerSerializer(data=request.data)
        if serializer.is_valid():
            telecaller = serializer.save(created_by=request.user)
            return Response({
                "code": 201,
                "message": "Telecaller created successfully",
                "data": TelecallerSerializer(telecaller).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)

class TelecallerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Telecaller.objects.get(pk=pk)
        except Telecaller.DoesNotExist:
            return None

    def get(self, request, pk):
        telecaller = self.get_object(pk)
        if not telecaller:
            return Response({
                "code": 404,
                "message": "Telecaller not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TelecallerSerializer(telecaller)
        return Response({
            "code": 200,
            "message": "Telecaller fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


    def patch(self, request, pk):
        telecaller = self.get_object(pk)
        if not telecaller:
            return Response({
                "code": 404,
                "message": "Telecaller not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TelecallerSerializer(telecaller, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "code": 200,
                "message": "Telecaller updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "code": 400,
            "message": "Invalid data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        telecaller = self.get_object(pk)
        if not telecaller:
            return Response({
                "code": 404,
                "message": "Telecaller not found"
            }, status=status.HTTP_404_NOT_FOUND)

        telecaller.delete()
        return Response({
            "code": 204,
            "message": "Telecaller deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)

