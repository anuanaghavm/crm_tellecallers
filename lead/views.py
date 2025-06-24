from rest_framework import generics, permissions
from .models import Lead
from .serializers import LeadSerializer

class LeadListCreateView(generics.ListCreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]  # or [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)

class LeadRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]  # or [permissions.AllowAny]
