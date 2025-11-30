from rest_framework import serializers
from .models import Experiment

class ExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = [
            'id',
            'prompt_template',  # Id (pk) de PromptTemplate
            'configurated_models',  # Lista de ids (pk) de ConfiguredModel
            'name',
            'num_runs',
            'execution_date',
            'status',
        ]
        read_only_fields = ['id', 'execution_date', 'status']


