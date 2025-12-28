from rest_framework import serializers

from llms.serializers import ConfiguredModelSerializer
from prompts.serializers import FeatureSerializer
from .models import Experiment, Run, MobileApp, MobileAppRanked, RankingCriteria

class MobileAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileApp
        fields = ['id', 'name', 'URL']
class MobileAppRankedSerializer(serializers.ModelSerializer):
    mobile_app = serializers.CharField(source='mobile_app.name', read_only=True)

    class Meta:
        model = MobileAppRanked
        fields = ['id', 'mobile_app', 'rank']

class RankingCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RankingCriteria
        fields = ['id', 'name', 'description']

class RunSerializer(serializers.ModelSerializer):
    mobile_app_rankings = MobileAppRankedSerializer(many=True, read_only=True)
    ranking_criteria = RankingCriteriaSerializer(many=True, read_only=True)
    configured_model = ConfiguredModelSerializer(read_only=True)
    feature = FeatureSerializer(read_only=True)

    class Meta:
        model = Run
        fields = ['id', 'elapsed_time', 'configured_model','feature', 'mobile_app_rankings', 'ranking_criteria']

class ExperimentSerializer(serializers.ModelSerializer):
    runs = RunSerializer(many=True, read_only=True)
    # can be used to show detailed info about configured models
    configured_models_detail = ConfiguredModelSerializer(source='configured_models', many=True, read_only=True)
    class Meta:
        model = Experiment
        fields = [
            'id',
            'prompt_template',  # Id (pk) de PromptTemplate
            'configured_models',  # Lista de ConfiguredModel
            'configured_models_detail',  # Detalles de ConfiguredModel
            'name',
            'num_runs',
            'execution_date',
            'status',
            'runs',  # Lista de Run
        ]
        read_only_fields = ['id', 'execution_date', 'status']
