# Create your views here.
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.db.models import ProtectedError
from .models import Template
from .serializers import TemplateSerializer

class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to handle ProtectedError and return a friendly message
        """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            # Count how many experiments are using this template
            protected_objects = e.protected_objects
            num_experiments = len(protected_objects)
            
            return Response(
                {
                    'message': f'This template cannot be deleted because it is being used by {num_experiments} experiment(s). Please delete or update the associated experiments first.',
                    'error': 'Cannot delete template',
                    'detail': f'Protected by {num_experiments} related object(s)',
                    'num_protected': num_experiments
                },
                status=status.HTTP_400_BAD_REQUEST
            )
