"""
Celery tasks for asynchronous experiment execution.
To use this, you'll need to:
1. Install celery: pip install celery redis
2. Configure Celery in your Django settings
3. Run a Celery worker: celery -A backend worker -l info
"""
import logging
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def execute_experiment_async(self, experiment_id: int):
    """
    Execute an experiment asynchronously.
    
    Args:
        experiment_id: The ID of the experiment to execute
        
    Returns:
        dict: Results of the experiment execution
    """
    try:
        # Import here to avoid circular imports
        from .models import Experiment
        from .services import ExperimentExecutionService
        
        logger.info(f"Starting async execution of experiment {experiment_id}")
        
        experiment = Experiment.objects.get(id=experiment_id)
        service = ExperimentExecutionService(experiment)
        results = service.execute()
        
        logger.info(f"Completed async execution of experiment {experiment_id}")
        
        return {
            "experiment_id": experiment_id,
            "status": "completed",
            "num_results": len(results)
        }
        
    except ObjectDoesNotExist:
        logger.error(f"Experiment {experiment_id} not found")
        raise
    
    except Exception as e:
        logger.error(f"Error executing experiment {experiment_id}: {str(e)}")
        # Retry the task with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
