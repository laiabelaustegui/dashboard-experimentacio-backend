from rest_framework import serializers
from .models import Experiment

class ExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = [
            'id',
            'prompt_template',  # Id (pk) de PromptTemplate
            'configuration',    # Id (pk) de Configuration
            'model',            # Id (pk) de LLM
            'name',
            'execution_date',
            'status',
        ]
        read_only_fields = ['id', 'execution_date', 'status']


