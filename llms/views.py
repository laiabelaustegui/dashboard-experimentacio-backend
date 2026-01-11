# Create your views here.

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.db.models import ProtectedError
from .models import LLM, Configuration, ConfiguredModel
from .serializers import LLMSerializer, ConfigurationSerializer, ConfiguredModelSerializer

class LLMViewSet(viewsets.ModelViewSet):
    queryset = LLM.objects.all()
    serializer_class = LLMSerializer
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to handle ProtectedError and return a friendly message
        """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            protected_objects = e.protected_objects
            num_protected = len(protected_objects)
            
            return Response(
                {
                    'message': f'This LLM cannot be deleted because it has {num_protected} configured model(s) associated. Please delete the configured models first.',
                    'error': 'Cannot delete LLM',
                    'detail': f'Protected by {num_protected} related object(s)',
                    'num_protected': num_protected
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class ConfigurationViewSet(viewsets.ModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to handle ProtectedError and return a friendly message
        """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            protected_objects = e.protected_objects
            num_protected = len(protected_objects)
            
            return Response(
                {
                    'message': f'This configuration cannot be deleted because it has {num_protected} configured model(s) associated. Please delete the configured models first.',
                    'error': 'Cannot delete configuration',
                    'detail': f'Protected by {num_protected} related object(s)',
                    'num_protected': num_protected
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class ConfiguredModelViewSet(viewsets.ModelViewSet):
    queryset = ConfiguredModel.objects.all()
    serializer_class = ConfiguredModelSerializer
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to handle ProtectedError and return a friendly message
        """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            protected_objects = e.protected_objects
            num_protected = len(protected_objects)
            
            return Response(
                {
                    'message': f'This configured model cannot be deleted because it is being used by {num_protected} experiment(s) or run(s). Please delete the associated experiments first.',
                    'error': 'Cannot delete configured model',
                    'detail': f'Protected by {num_protected} related object(s)',
                    'num_protected': num_protected
                },
                status=status.HTTP_400_BAD_REQUEST
            )