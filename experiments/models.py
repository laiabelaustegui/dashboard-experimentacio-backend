from django.db import models
from prompts.models import Template as PromptTemplate
from llms.models import LLM, Configuration

# Create your models here.

class Experiment(models.Model):
    class Status(models.TextChoices):
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    prompt_template = models.ForeignKey(PromptTemplate, on_delete=models.CASCADE)
    configuration = models.ForeignKey(Configuration, on_delete=models.CASCADE)
    model = models.ForeignKey(LLM, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    execution_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.RUNNING,
    )
    class Meta:
        unique_together = ('prompt_template', 'configuration', 'model')
    
    def __str__(self):
        return self.name

# class Run(models.Model):
#     experiment = models.ForeignKey('Experiment', on_delete=models.CASCADE, related_name='runs')
#     time_of_execution = models.DateTimeField()

#     def __str__(self):
#         return f"Run {self.id} for {self.experiment.name}"