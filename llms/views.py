# Create your views here.

from rest_framework import viewsets
from .models import LLM, Configuration, ConfiguredModel
from .serializers import LLMSerializer, ConfigurationSerializer, ConfiguredModelSerializer

class LLMViewSet(viewsets.ModelViewSet):
    queryset = LLM.objects.all()
    serializer_class = LLMSerializer

class ConfigurationViewSet(viewsets.ModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer

class ConfiguredModelViewSet(viewsets.ModelViewSet):
    queryset = ConfiguredModel.objects.all()
    serializer_class = ConfiguredModelSerializer