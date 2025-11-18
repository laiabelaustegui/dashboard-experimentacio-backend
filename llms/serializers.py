from rest_framework import serializers
from .models import LLM

class LLMSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLM
        fields = '__all__'
