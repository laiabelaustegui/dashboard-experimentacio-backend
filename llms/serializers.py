from rest_framework import serializers
from .models import LLM, Configuration, ConfiguredModel

class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuration
        fields = '__all__'

class LLMSerializer(serializers.ModelSerializer):
    configurations = ConfigurationSerializer(many=True, read_only=True)

    class Meta:
        model = LLM
        fields = ['id', 'name', 'provider', 'API_endpoint', 'API_key', 'creation_date', 'configurations']
        extra_kwargs = {
            'API_key': {'write_only': True},
        }
        
class ConfiguredModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguredModel
        fields = ['id', 'llm', 'configuration', 'short_name']
