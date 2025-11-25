from django.db import models
from .utils import encrypt, decrypt

# Create your models here.
class Configuration(models.Model):
    name = models.CharField(max_length=100, default="Default Configuration")
    temperature = models.FloatField(default=0.7)
    topP = models.FloatField(null=True, blank=True)

    def __str__(self):
        return str(self.name)
    
class LLM(models.Model):
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=100)
    API_endpoint = models.URLField(null=True, blank=True)
    API_key = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)
    configurations = models.ManyToManyField(Configuration, blank=True, related_name='llms')

    def save(self, *args, **kwargs):
        if not self.API_key.startswith('gAAAA'):  # evita cifrar dos veces
            self.API_key = encrypt(self.API_key)
        super().save(*args, **kwargs)

    def get_api_key(self):
        return decrypt(self.API_key)

    def __str__(self):
        return str(self.name)