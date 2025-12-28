from django.db import models
from prompts.models import Template as PromptTemplate, Feature
from llms.models import ConfiguredModel
# Create your models here.

class Experiment(models.Model):
    class Status(models.TextChoices):
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    prompt_template = models.ForeignKey(PromptTemplate, on_delete=models.PROTECT)
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
            models.UniqueConstraint(fields=['mobile_app', 'run'], name='unique_app_per_run'),
        ]
        ordering = ['rank']

    def __str__(self):
        return f"{self.mobile_app.name} ranked {self.rank} for {self.run}"