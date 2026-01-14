from django.db import models
from prompts.models import Template as PromptTemplate, Feature
from llms.models import ConfiguredModel
from .experiment_states import ExperimentStateContext
# Create your models here.

class Experiment(models.Model):
    class Status(models.TextChoices):
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    prompt_template = models.ForeignKey(PromptTemplate, on_delete=models.CASCADE)
    configured_models = models.ManyToManyField(ConfiguredModel, related_name='experiments')
    name = models.CharField(max_length=100, unique=True)
    num_runs = models.PositiveIntegerField(default=1)
    execution_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.RUNNING,
    )
    
    def __str__(self):
        return str(self.name)
    
    def get_state_context(self) -> ExperimentStateContext:
        """Get or create the state context for this experiment."""
        if not hasattr(self, '_state_context') or self._state_context is None:
            self._state_context = ExperimentStateContext(self)
        return self._state_context
    
    def can_execute(self) -> bool:
        """Check if the experiment can be executed."""
        return self.get_state_context().can_execute()
    
    def mark_as_running(self, save: bool = True) -> bool:
        """Transition to running state. Returns True if successful."""
        success = self.get_state_context().transition_to_running()
        if success and save:
            self.save(update_fields=['status'])
        return success
    
    def mark_as_completed(self, save: bool = True) -> bool:
        """Transition to completed state. Returns True if successful."""
        success = self.get_state_context().transition_to_completed()
        if success and save:
            self.save(update_fields=['status'])
        return success
    
    def mark_as_failed(self, save: bool = True) -> bool:
        """Transition to failed state. Returns True if successful."""
        success = self.get_state_context().transition_to_failed()
        if success and save:
            self.save(update_fields=['status'])
        return success


class Run(models.Model):
    experiment = models.ForeignKey('Experiment', on_delete=models.CASCADE, related_name='runs')
    configured_model = models.ForeignKey(  # nuevo campo
        ConfiguredModel,
        on_delete=models.PROTECT,  # o CASCADE, según quieras
        related_name='runs',
        null=False,
    )
    feature = models.ForeignKey(Feature, on_delete=models.PROTECT, related_name='runs')
    elapsed_time = models.FloatField(null=True, blank=True)
    apps = models.ManyToManyField('MobileApp', through='MobileAppRanked', related_name='runs')

    def __str__(self):
        return f"Run for {self.experiment.name}"
    
class RankingCriteria(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    #Para forzar “mínimo 1 criterio por run”, igual que antes, debes validarlo en lógica (serializer o clean()), no a nivel de FK.
    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE,
        related_name='ranking_criteria',
        null=True,        # permite 0 runs (criterio no asociado aún) debe revisarse en un serializer o vista
        blank=True
    )
    def __str__(self):
        return f"Criterion: {self.name}"

class MobileApp(models.Model):
    name = models.CharField(max_length=100)
    URL = models.URLField()
    def __str__(self):
        return f"Mobile App: {self.name}"
    
class MobileAppRanked(models.Model):
    mobile_app = models.ForeignKey(MobileApp, on_delete=models.CASCADE, related_name='rankings')
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name='mobile_app_rankings')
    rank = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['mobile_app', 'run', 'rank'], name='unique_app_rank_per_run'),
        ]
        ordering = ['rank']

    def __str__(self):
        return f"{self.mobile_app.name} ranked {self.rank} for {self.run}"