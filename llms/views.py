# Create your views here.

from rest_framework import viewsets
from .models import LLM
from .serializers import LLMSerializer

class LLMViewSet(viewsets.ModelViewSet):
    queryset = LLM.objects.all()
    serializer_class = LLMSerializer
