from rest_framework import generics, permissions
from .models import Lead
from .serializers import LeadSerializer

class LeadListCreateView(generics.ListCreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]  # Or use AllowAny if public

    def perform_create(self, serializer):
        serializer.save()  # ✅ No user passed


class LeadRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]  # Or use AllowAny
