# Create your views here.
from rest_framework import viewsets
from .models import Template
from .serializers import TemplateSerializer

class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
