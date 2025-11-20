from django.db import models

# Create your models here.
class Prompt(models.Model):
    text = models.TextField()

    class Meta:
        abstract = True  # ¡Esto es esencial!

    def __str__(self):
        return self.text

class SystemPrompt(Prompt):
    schema = models.JSONField()  # campo específico

class UserPrompt(Prompt):
    pass  # sin campos adicionales por ahora

class Template(models.Model):
    name = models.CharField(max_length=100)
    creation_date = models.DateTimeField(auto_now_add=True)
    system_prompt = models.OneToOneField(
        'SystemPrompt', 
        on_delete=models.CASCADE,
        related_name='template_system'
    )
    user_prompt = models.OneToOneField(
        'UserPrompt', 
        on_delete=models.CASCADE,
        related_name='template_user'
    )

    def __str__(self):
        return self.name