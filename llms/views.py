# Create your views here.

from rest_framework import viewsets
from .models import LLM, Configuration
from .serializers import LLMSerializer, ConfigurationSerializer

class LLMViewSet(viewsets.ModelViewSet):
    queryset = LLM.objects.all()
    serializer_class = LLMSerializer

class ConfigurationViewSet(viewsets.ModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer

