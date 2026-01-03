from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.db.models import ProtectedError
import logging

from .models import Experiment, MobileApp, RankingCriteria
from .serializers import ExperimentSerializer, MobileAppSerializer, RankingCriteriaSerializer
from .services import ExperimentExecutionService

logger = logging.getLogger(__name__)


class ExperimentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing experiments.
    
    Supports synchronous execution by default.
    For async execution, uncomment the task import and use execute_experiment_async.
    """
    http_method_names = ['get', 'post', 'delete']
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer

    def create(self, request, *args, **kwargs):
        """
        Create and execute a new experiment.
        
        To enable async execution:
        1. Install celery: pip install celery redis
        2. Uncomment the async code below
        3. Set up Celery in your Django settings
        """
        serializer = ExperimentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        experiment = serializer.save()
        
        # Synchronous execution (current behavior)
        try:
            service = ExperimentExecutionService(experiment)
            results = service.execute()
            
            logger.info(f"Experiment {experiment.id} completed with {len(results)} runs")
            
            return Response({
                "experiment": ExperimentSerializer(experiment).data,
                "num_runs": len(results)
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            # Validation errors (no models, no features, etc.)
            logger.warning(f"Validation error for experiment {experiment.id}: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error for experiment {experiment.id}: {str(e)}")
            return Response(
                {"error": f"Experiment execution failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Asynchronous execution (uncomment to use)
        # Requires Celery setup and Redis running
        # try:
        #     from .tasks import execute_experiment_async
        #     task = execute_experiment_async.delay(experiment.id)
        #     
        #     return Response({
        #         "experiment": ExperimentSerializer(experiment).data,
        #         "task_id": task.id,
        #         "message": "Experiment queued for execution"
        #     }, status=status.HTTP_202_ACCEPTED)
        # except ImportError:
        #     logger.error("Celery not configured. Install celery to use async execution.")
        #     return Response(
        #         {"error": "Async execution not available. Please configure Celery."},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )
    
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
                    'message': f'This experiment cannot be deleted because it has {num_protected} related run(s) or other dependencies. This is unusual - experiments should normally be deletable.',
                    'error': 'Cannot delete experiment',
                    'detail': f'Protected by {num_protected} related object(s)',
                    'num_protected': num_protected
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class MobileAppViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MobileApp.objects.all()
    serializer_class = MobileAppSerializer

class RankingCriteriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RankingCriteria.objects.all()
    serializer_class = RankingCriteriaSerializer
