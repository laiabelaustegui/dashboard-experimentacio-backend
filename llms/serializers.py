from rest_framework import serializers
from .models import LLM, Configuration

class LLMSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLM
        fields = '__all__'

class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuration
        fields = '__all__'


